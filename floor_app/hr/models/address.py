from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from django.db.models import Q
from ..mixins import HRAuditMixin, HRSoftDeleteMixin
import phonenumbers
import pycountry
from ...mixins import PublicIdMixin

try:
    # Django 3.1+
    from django.db.models import JSONField
except Exception:  # pragma: no cover
    from django.contrib.postgres.fields import JSONField  # fallback if older + Postgres


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


class HRAddress(PublicIdMixin, HRAuditMixin, HRSoftDeleteMixin):
    """
    Global postal address with optional geolocation.
    Supports structured fields compatible with Saudi National Address (SPL).
    """

    # === Core lines ===
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True, default="")
    city          = models.CharField(max_length=120, blank=True, default="")
    state_region  = models.CharField(max_length=120, blank=True, default="")
    postal_code   = models.CharField(max_length=20,  blank=True, default="")
    country_iso2  = models.CharField(max_length=2, choices=COUNTRY_CHOICES)

    # === Geo ===
    latitude      = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude     = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # === Usage/labels ===
    KIND = (("HOME", "Home"), ("OFFICE", "Office"), ("BILLING", "Billing"), ("SHIPPING", "Shipping"), ("OTHER", "Other"))
    kind = models.CharField(max_length=10, choices=KIND, default="OTHER")
    USE  = (("PERSONAL", "Personal"), ("BUSINESS", "Business"))
    use  = models.CharField(max_length=8, choices=USE, default="BUSINESS")
    is_primary_hint = models.BooleanField(default=False)
    label           = models.CharField(max_length=64, blank=True, default="")

    # === Structured (global) + KSA fields ===
    address_kind = models.CharField(
        max_length=8,
        choices=(("STREET", "Street address"), ("PO_BOX", "PO Box")),
        default="STREET",
    )
    street_name       = models.CharField(max_length=200, blank=True, default="")
    building_number   = models.CharField(max_length=16,  blank=True, default="")
    unit_number       = models.CharField(max_length=16,  blank=True, default="")
    neighborhood      = models.CharField(max_length=120, blank=True, default="")
    additional_number = models.CharField(max_length=8,   blank=True, default="")  # KSA 4 digits
    po_box            = models.CharField(max_length=20,  blank=True, default="")
    components        = JSONField(blank=True, null=True)

    class Meta:
        db_table = "hr_address"
        constraints = [
            # Street-address uniqueness (case-insensitive) when address_kind=STREET
            models.UniqueConstraint(
                Lower("country_iso2"), Lower("city"), Lower("neighborhood"),
                Lower("street_name"), Lower("building_number"), Lower("unit_number"),
                name="uq_hr_address_street_tuple_ci",
                condition=Q(address_kind="STREET"),
            ),
            # PO Box uniqueness when address_kind=PO_BOX
            models.UniqueConstraint(
                Lower("country_iso2"), Lower("city"), Lower("po_box"),
                name="uq_hr_address_pobox_tuple_ci",
                condition=Q(address_kind="PO_BOX"),
            ),
        ]

    def clean(self):
        super().clean()

        # Lat/lng sanity
        if self.latitude is not None and not (-90 <= float(self.latitude) <= 90):
            raise ValidationError("Latitude must be between -90 and 90.")
        if self.longitude is not None and not (-180 <= float(self.longitude) <= 180):
            raise ValidationError("Longitude must be between -180 and 180.")

        # PO Box vs Street minimal requirements
        if self.address_kind == "PO_BOX":
            if not self.po_box:
                raise ValidationError("PO Box is required when address kind is PO Box.")
        else:
            if not (self.address_line1 or (self.street_name and self.building_number)):
                raise ValidationError("Provide address line1 or street name + building number.")

        # KSA National Address rules (only for SA)
        if (self.country_iso2 or "").upper() == "SA":
            import re
            if self.postal_code and not re.fullmatch(r"\d{5}", self.postal_code):
                raise ValidationError("Saudi postal code must be 5 digits.")
            if self.additional_number and not re.fullmatch(r"\d{4}", self.additional_number):
                raise ValidationError("Saudi additional number must be 4 digits.")
            if self.address_kind == "STREET":
                required = [
                    ("street_name", self.street_name),
                    ("building_number", self.building_number),
                    ("neighborhood", self.neighborhood),
                    ("city", self.city),
                ]
                missing = [n for n, v in required if not v]
                if missing:
                    raise ValidationError(f"KSA street address: missing {', '.join(missing)}.")

    def __str__(self):
        parts = [
            (self.address_line1 or f"{self.building_number} {self.street_name}".strip()),
            self.neighborhood, self.city, self.state_region, self.postal_code, self.country_iso2
        ]
        return ", ".join([p for p in parts if p])
