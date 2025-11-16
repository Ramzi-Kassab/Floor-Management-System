from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from django.db.models import Q, Index

from floor_app.mixins import HRAuditMixin, HRSoftDeleteMixin
from floor_app.mixins import PublicIdMixin
from django.conf import settings

import hashlib
import phonenumbers
import pycountry

# Optional Hijri support (pip install hijri-converter)
try:
    from hijri_converter import Gregorian, Hijri
    _HAS_HIJRI = True
except Exception:  # pragma: no cover
    _HAS_HIJRI = False


def _country_choices():
    choices = []
    for iso in sorted(phonenumbers.SUPPORTED_REGIONS):
        try:
            name = pycountry.countries.get(alpha_2=iso).name
        except Exception:
            name = iso
        choices.append((iso, f"{name} ({iso})"))
    return choices


COUNTRY_CHOICES = _country_choices()
GENDER_CHOICES = (("MALE", "Male"), ("FEMALE", "Female"))


class HRPeople(PublicIdMixin, HRAuditMixin, HRSoftDeleteMixin):
    """
    Canonical person (identity only).
    - national_id: always present and belongs to primary_nationality_iso2
    - iqama_number: required for non-Saudis; must be empty for Saudis
    """
    # Legal names (English)
    first_name_en  = models.CharField(max_length=120, help_text="First name in English")
    middle_name_en = models.CharField(max_length=120, blank=True, default="", help_text="Middle name in English (optional)")
    last_name_en   = models.CharField(max_length=120, help_text="Last name in English")

    # Legal names (Arabic)
    first_name_ar  = models.CharField(max_length=120, blank=True, default="", help_text="First name in Arabic (optional)")
    middle_name_ar = models.CharField(max_length=120, blank=True, default="", help_text="Middle name in Arabic (optional)")
    last_name_ar   = models.CharField(max_length=120, blank=True, default="", help_text="Last name in Arabic (optional)")

    # DoB (either can be entered; the other is auto-converted)
    date_of_birth       = models.DateField(null=True, blank=True)             # Gregorian
    date_of_birth_hijri = models.CharField(max_length=10, blank=True, default="")  # YYYY-MM-DD

    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)

    # Nationality
    primary_nationality_iso2 = models.CharField(max_length=2, choices=COUNTRY_CHOICES)

    # IDs
    national_id = models.CharField(max_length=64, db_index=True)              # always required

    iqama_number = models.CharField(max_length=10, blank=True, default="", db_index=True)  # req. for non-SA
    iqama_expiry = models.DateField(null=True, blank=True)

    # Photo
    photo = models.ImageField(upload_to="hr/people/photos/", blank=True, null=True)

    # === Identity Verification ===
    MARITAL_STATUS = (
        ("SINGLE", "Single"),
        ("MARRIED", "Married"),
        ("DIVORCED", "Divorced"),
        ("WIDOWED", "Widowed"),
    )
    marital_status = models.CharField(
        max_length=16,
        choices=MARITAL_STATUS,
        blank=True,
        default="",
        help_text="Marital status"
    )

    identity_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Has the identity been verified and authenticated?"
    )
    identity_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        help_text="Timestamp of identity verification"
    )
    identity_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_hr_people",
        editable=False,
        help_text="User who verified the identity"
    )

    # Dedupe helper (normalized names + DOB), SHA1 hex
    name_dob_hash = models.CharField(max_length=40, editable=False, db_index=True)

    class Meta:
        db_table = "hr_people"
        constraints = [
            # national_id unique if provided (case-insensitive)
            models.UniqueConstraint(
                Lower("national_id"),
                name="uq_hr_people_national_id_ci",
                condition=~Q(national_id=""),
            ),
            # iqama unique if provided (case-insensitive)
            models.UniqueConstraint(
                Lower("iqama_number"),
                name="uq_hr_people_iqama_ci",
                condition=~Q(iqama_number=""),
            ),
        ]
        indexes = [Index(fields=["name_dob_hash"], name="ix_hr_people_namedob")]

    # ---------- helpers ----------
    @staticmethod
    def _norm(s: str) -> str:
        return (s or "").strip().lower()

    def _compute_hash(self) -> str:
        parts = [
            self._norm(self.first_name_en), self._norm(self.middle_name_en), self._norm(self.last_name_en),
            self._norm(self.first_name_ar), self._norm(self.middle_name_ar), self._norm(self.last_name_ar),
            self.date_of_birth.isoformat() if self.date_of_birth else "",
        ]
        return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()

    def _compute_hijri_from_greg(self) -> str:
        if not _HAS_HIJRI or not self.date_of_birth:
            return ""
        try:
            g = Gregorian(self.date_of_birth.year, self.date_of_birth.month, self.date_of_birth.day)
            h = g.to_hijri()
            return f"{h.year:04d}-{h.month:02d}-{h.day:02d}"
        except Exception:
            return ""

    def _compute_greg_from_hijri(self, hijri_str: str):
        """Return datetime.date or None."""
        if not _HAS_HIJRI or not hijri_str:
            return None
        try:
            y, m, d = [int(x) for x in hijri_str.split("-")]
            g = Hijri(y, m, d).to_gregorian()
            return g.datetimedate()
        except Exception:
            return None

    # ---------- validation ----------
    def clean(self):
        super().clean()

        # Required English names
        if not self.first_name_en or not self.last_name_en:
            raise ValidationError("English first and last name are required.")

        # Normalize IDs
        self.national_id = (self.national_id or "").strip()
        self.iqama_number = (self.iqama_number or "").strip()

        if not self.national_id:
            raise ValidationError("National ID is required.")

        # DoB ↔ Hijri sync
        if self.date_of_birth and not self.date_of_birth_hijri:
            self.date_of_birth_hijri = self._compute_hijri_from_greg()
        elif self.date_of_birth_hijri and not self.date_of_birth:
            if not _HAS_HIJRI:
                raise ValidationError("Hijri date provided but hijri-converter is not installed.")
            gdate = self._compute_greg_from_hijri(self.date_of_birth_hijri)
            if not gdate:
                raise ValidationError("Invalid Hijri date format; expected YYYY-MM-DD.")
            self.date_of_birth = gdate
        elif self.date_of_birth and self.date_of_birth_hijri:
            computed = self._compute_hijri_from_greg()
            if computed and computed != self.date_of_birth_hijri:
                raise ValidationError("Gregorian DoB and Hijri DoB do not match.")

        # SA vs non-SA rules + basic patterns
        import re
        if (self.primary_nationality_iso2 or "").upper() == "SA":
            # Saudis: must not have Iqama; National ID must be SA pattern
            if self.iqama_number:
                raise ValidationError("Saudis cannot have an Iqama number.")
            if not re.fullmatch(r"1\d{9}", self.national_id):
                raise ValidationError("Saudi National ID must be 10 digits starting with 1.")
        else:
            # Non-Saudis: Iqama is required (Saudi residency)
            if not self.iqama_number:
                raise ValidationError("Iqama number is required for non-Saudis.")
            if not re.fullmatch(r"2\d{9}", self.iqama_number):
                raise ValidationError("Saudi Iqama must be 10 digits starting with 2.")

        # Dedupe hash
        self.name_dob_hash = self._compute_hash()

    def save(self, *args, **kwargs):
        # Keep Hijri/Gregorian cache in sync even if full_clean wasn't invoked
        if self.date_of_birth and not self.date_of_birth_hijri:
            self.date_of_birth_hijri = self._compute_hijri_from_greg()
        if self.date_of_birth_hijri and not self.date_of_birth and _HAS_HIJRI:
            gdate = self._compute_greg_from_hijri(self.date_of_birth_hijri)
            if gdate:
                self.date_of_birth = gdate
        if not self.name_dob_hash:
            self.name_dob_hash = self._compute_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name_en} {self.last_name_en}".strip()

    def get_full_name_en(self):
        """Get full English name"""
        parts = [self.first_name_en, self.middle_name_en, self.last_name_en]
        return " ".join(p for p in parts if p).strip()
