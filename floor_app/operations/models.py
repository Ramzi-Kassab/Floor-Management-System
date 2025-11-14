"""
Generic operations models for the floor management system.
These models serve multiple modules: HR, facilities, locations, etc.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from django.db.models import Q
import phonenumbers
import pycountry

try:
    from django.db.models import JSONField
except Exception:
    from django.contrib.postgres.fields import JSONField

from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


def _country_choices():
    """Generate country choices from pycountry."""
    choices = []
    for iso in sorted(phonenumbers.SUPPORTED_REGIONS):
        try:
            name = pycountry.countries.get(alpha_2=iso).name
        except Exception:
            name = iso
        choices.append((iso, f"{name} ({iso})"))
    return choices


COUNTRY_CHOICES = _country_choices()


class Address(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Generic address model for all entities in the system.

    Can be used for:
    - HR People (personal, office, billing addresses)
    - Wells and Rigs (operational locations)
    - Company Facilities (offices, warehouses, plants)
    - Any other location-based entity

    Uses structured fields for professional address standardization,
    particularly for Saudi National Address (SPL) compliance.
    """

    # === Core address lines ===
    address_line1 = models.CharField(
        max_length=200,
        help_text="Primary address line (street, building, etc.)"
    )
    address_line2 = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Secondary address line (apartment, suite, etc.)"
    )
    city = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="City/Town name"
    )
    state_region = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="State, Province, or Region"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Postal code or ZIP code"
    )
    country_iso2 = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        help_text="Country code (ISO 3166-1 alpha-2)"
    )

    # === Geolocation ===
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude coordinate"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude coordinate"
    )

    # === Address structure type ===
    ADDRESS_KIND = (
        ("STREET", "Street Address"),
        ("PO_BOX", "PO Box"),
    )
    address_kind = models.CharField(
        max_length=8,
        choices=ADDRESS_KIND,
        default="STREET",
        help_text="Type of address (street address or PO box)"
    )

    # === Structured Saudi National Address (SPL) fields ===
    street_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Street name (for KSA National Address)"
    )
    building_number = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Building number (for KSA National Address)"
    )
    unit_number = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Unit/Apartment/Office number"
    )
    neighborhood = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Neighborhood name (for KSA National Address)"
    )
    additional_number = models.CharField(
        max_length=8,
        blank=True,
        default="",
        help_text="Additional number - 4 digits (for KSA National Address)"
    )
    po_box = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="PO Box number (when address_kind=PO_BOX)"
    )

    # === Flexible storage for additional components ===
    components = JSONField(
        blank=True,
        null=True,
        help_text="Additional address components (JSON format)"
    )

    # === Metadata ===
    label = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Label for this address (e.g., 'Home', 'Well #5', 'Rig Alpha')"
    )

    VERIFICATION_STATUS = (
        ("UNVERIFIED", "Unverified"),
        ("VERIFIED", "Verified"),
        ("INVALID", "Invalid"),
    )
    verification_status = models.CharField(
        max_length=16,
        choices=VERIFICATION_STATUS,
        default="UNVERIFIED",
        help_text="Address verification status"
    )

    accessibility_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes about accessibility (wheelchair, elevator, parking, etc.)"
    )

    # === HR-specific fields (for HR People addresses) ===
    hr_person = models.ForeignKey(
        "hr.HRPeople",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="addresses",
        help_text="HR Person associated with this address (if applicable)"
    )

    HR_KIND = (
        ("HOME", "Home"),
        ("OFFICE", "Office"),
        ("BILLING", "Billing"),
        ("SHIPPING", "Shipping"),
        ("OTHER", "Other"),
    )
    hr_kind = models.CharField(
        max_length=10,
        choices=HR_KIND,
        blank=True,
        default="",
        help_text="Purpose/type of this address (for HR use)"
    )

    HR_USE = (
        ("PERSONAL", "Personal"),
        ("BUSINESS", "Business"),
    )
    hr_use = models.CharField(
        max_length=8,
        choices=HR_USE,
        blank=True,
        default="",
        help_text="Personal or business use (for HR use)"
    )

    is_primary_hint = models.BooleanField(
        default=False,
        help_text="Is this the primary address for the HR person?"
    )

    class Meta:
        db_table = "operations_address"
        ordering = ["country_iso2", "city", "address_line1"]
        indexes = [
            models.Index(fields=["country_iso2", "city", "postal_code"]),
            models.Index(fields=["verification_status", "is_deleted"]),
            models.Index(fields=["hr_person", "hr_kind"]),
            models.Index(fields=["hr_person", "is_primary_hint"]),
        ]
        constraints = [
            # Street address uniqueness (case-insensitive) when address_kind=STREET
            models.UniqueConstraint(
                Lower("country_iso2"),
                Lower("city"),
                Lower("neighborhood"),
                Lower("street_name"),
                Lower("building_number"),
                Lower("unit_number"),
                name="uq_operations_address_street_tuple_ci",
                condition=Q(address_kind="STREET", is_deleted=False),
            ),
            # PO Box uniqueness when address_kind=PO_BOX
            models.UniqueConstraint(
                Lower("country_iso2"),
                Lower("city"),
                Lower("po_box"),
                name="uq_operations_address_pobox_tuple_ci",
                condition=Q(address_kind="PO_BOX", is_deleted=False),
            ),
        ]

    def clean(self):
        """Validate address fields based on address_kind and country."""
        super().clean()

        # Latitude/Longitude sanity checks
        if self.latitude is not None and not (-90 <= float(self.latitude) <= 90):
            raise ValidationError("Latitude must be between -90 and 90.")
        if self.longitude is not None and not (-180 <= float(self.longitude) <= 180):
            raise ValidationError("Longitude must be between -180 and 180.")

        # PO Box vs Street minimal requirements
        if self.address_kind == "PO_BOX":
            if not self.po_box:
                raise ValidationError("PO Box number is required when address kind is 'PO Box'.")
        else:
            if not (self.address_line1 or (self.street_name and self.building_number)):
                raise ValidationError(
                    "Provide either address line 1 or (street name + building number)."
                )

        # KSA National Address rules (only for Saudi Arabia)
        if (self.country_iso2 or "").upper() == "SA":
            import re

            if self.postal_code and not re.fullmatch(r"\d{5}", self.postal_code):
                raise ValidationError("Saudi postal code must be exactly 5 digits.")

            if self.additional_number and not re.fullmatch(r"\d{4}", self.additional_number):
                raise ValidationError("Saudi additional number must be exactly 4 digits.")

            if self.address_kind == "STREET":
                required_fields = {
                    "street_name": self.street_name,
                    "building_number": self.building_number,
                    "neighborhood": self.neighborhood,
                    "city": self.city,
                }
                missing = [name for name, value in required_fields.items() if not value]
                if missing:
                    raise ValidationError(
                        f"For Saudi street addresses, these fields are required: {', '.join(missing)}"
                    )

    def __str__(self):
        """Return a human-readable address string."""
        parts = [
            self.address_line1 or f"{self.building_number} {self.street_name}".strip(),
            self.neighborhood,
            self.city,
            self.state_region,
            self.postal_code,
            self.country_iso2,
        ]
        return ", ".join([p for p in parts if p])

    @property
    def is_saudi_address(self):
        """Check if this is a Saudi address."""
        return (self.country_iso2 or "").upper() == "SA"

    @property
    def full_address(self):
        """Return the complete formatted address."""
        lines = []
        if self.address_line1:
            lines.append(self.address_line1)
        if self.address_line2:
            lines.append(self.address_line2)
        if self.neighborhood:
            lines.append(f"{self.neighborhood}, {self.city}")
        elif self.city:
            lines.append(self.city)
        if self.state_region:
            lines.append(self.state_region)
        if self.postal_code:
            lines.append(self.postal_code)
        if self.country_iso2:
            lines.append(self.country_iso2)
        return "\n".join(lines)
