import phonenumbers, pycountry
from django.db import models
from django.core.validators import RegexValidator
from django.db.models import Q
from django.core.exceptions import ValidationError
from ..mixins import HRAuditMixin, HRSoftDeleteMixin

_cc_validator = RegexValidator(r"^\+\d{1,4}$", "Use a valid country calling code like +966, +1, +44")
_digits = RegexValidator(r"^\d{2,20}$", "Digits only")

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


class HRPhone(HRAuditMixin, HRSoftDeleteMixin):
    country_iso2    = models.CharField(max_length=2, choices=COUNTRY_CHOICES, blank=True, default="")
    calling_code    = models.CharField(max_length=5, validators=[_cc_validator], blank=True, default="")
    national_number = models.CharField(max_length=20, validators=[_digits], blank=True, default="")
    phone_e164      = models.CharField(max_length=20, db_index=True, editable=False)

    CHANNEL = (("CALL", "Call"), ("WHATS", "Whats"), ("BOTH", "Call/Whats"))
    channel = models.CharField(max_length=8, choices=CHANNEL, default="CALL")

    KIND = (("MOBILE", "Mobile"), ("LAND", "Landline"))
    kind = models.CharField(max_length=8, choices=KIND, default="MOBILE")
    extension = models.CharField(max_length=10, blank=True, default="")  # landline only

    USE = (("PERSONAL", "Personal"), ("BUSINESS", "Business"))
    use = models.CharField(max_length=8, choices=USE, default="BUSINESS")

    is_primary_hint = models.BooleanField(default=False)
    label = models.CharField(max_length=32, blank=True, default="")
    person = models.ForeignKey(
        "HRPeople",
        on_delete=models.PROTECT,
        related_name="phones",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "hr_phone"
        constraints = [
            models.CheckConstraint(check=Q(kind="LAND") | Q(extension=""), name="ck_hr_phone_ext_only_for_land"),
            models.UniqueConstraint(fields=["phone_e164", "extension"], name="uq_hr_phone_e164_ext"),
        ]

    def clean(self):
        # Landline rule
        if self.kind == "LAND" and self.channel in {"WHATS", "BOTH"}:
            raise ValidationError("Landline can only be 'Call'.")

        # Country -> calling code (authoritative)
        region = (self.country_iso2 or "").upper() or None
        if region:
            try:
                cc = phonenumbers.country_code_for_region(region)
                if cc:
                    self.calling_code = f"+{cc}"
            except Exception:
                pass

        # Compute & validate E.164
        if not self.national_number:
            return  # allow blank legacy rows

        raw = (self.calling_code or "") + self.national_number
        try:
            pn = phonenumbers.parse(raw, region)
            if not phonenumbers.is_valid_number(pn):
                raise ValidationError("Invalid phone number for the selected country/calling code.")
            self.phone_e164 = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
            if not region:
                parsed_region = phonenumbers.region_code_for_number(pn)
                if parsed_region:
                    self.country_iso2 = parsed_region
        except phonenumbers.NumberParseException as e:
            raise ValidationError(f"Phone parse error: {e}")

    def clone_with_extension(self, extension_value):
        clone = HRPhone(
            country_iso2=self.country_iso2,
            calling_code=self.calling_code,
            national_number=self.national_number,
            channel=self.channel,
            kind=self.kind,
            extension=extension_value,
            use=self.use,
            is_primary_hint=self.is_primary_hint,
            label=self.label,
        )
        clone.clean()
        return clone

    def __str__(self):
        ext = f" ext {self.extension}" if self.extension else ""
        base = self.phone_e164 or (self.calling_code + self.national_number)
        return f"{base}{ext}"
