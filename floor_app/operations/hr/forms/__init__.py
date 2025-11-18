from django import forms
from django.forms import inlineformset_factory

from ..models import HRPeople, HREmployee, HRPhone, HREmail, Address


class HRPeopleForm(forms.ModelForm):
    class Meta:
        model = HRPeople
        fields = [
            # English names (organized logically)
            "first_name_en",
            "middle_name_en",
            "last_name_en",
            # Arabic names
            "first_name_ar",
            "middle_name_ar",
            "last_name_ar",
            # Personal info
            "gender",
            "date_of_birth",
            "date_of_birth_hijri",
            # Nationality & IDs
            "primary_nationality_iso2",
            "national_id",
            "iqama_number",
            "iqama_expiry",
            # Media
            "photo",
        ]


class HREmployeeForm(forms.ModelForm):
    class Meta:
        model = HREmployee
        fields = [
            # Basic Information
            "person",
            "user",
            "employee_no",
            "status",
            # Job Assignment
            "position",
            "department",
            # Contract Type
            "contract_type",
            # Contract Duration (for fixed-term contracts)
            "contract_start_date",
            "contract_end_date",
            "contract_renewal_date",
            # Probation
            "probation_end_date",
            "probation_status",
            # Employment Dates
            "hire_date",
            "termination_date",
            # Work Schedule
            "work_days_per_week",
            "hours_per_week",
            "shift_pattern",
            # Compensation
            "salary_grade",
            "monthly_salary",
            "benefits_eligible",
            "overtime_eligible",
            # Leave Entitlements
            "annual_leave_days",
            "sick_leave_days",
            "special_leave_days",
            # Employment Details
            "employment_category",
            "employment_status",
            "supervisor",
            "cost_center",
        ]


HRPhoneFormSet = inlineformset_factory(
    HRPeople,
    HRPhone,
    fields="__all__",
    exclude=("person", "created_at", "created_by", "updated_at", "updated_by", "is_deleted", "deleted_at"),
    extra=1,
    can_delete=True,
)

HREmailFormSet = inlineformset_factory(
    HRPeople,
    HREmail,
    fields="__all__",
    exclude=("person", "created_at", "created_by", "updated_at", "updated_by", "is_deleted", "deleted_at"),
    extra=1,
    can_delete=True,
)

AddressFormSet = inlineformset_factory(
    HRPeople,
    Address,
    fields="__all__",
    exclude=(
        "hr_person",  # Set automatically from person_id
        "created_at", "created_by", "updated_at", "updated_by", "is_deleted", "deleted_at",  # Audit fields
        "latitude", "longitude",  # Map integration not supported in formsets
        "verification_status",  # Auto-set to UNVERIFIED on creation; can be updated in admin
        "hr_kind", "hr_use", "is_primary_hint", "label", "accessibility_notes", "components"  # HR-specific fields, optional or admin-only
    ),
    extra=1,
    can_delete=True,
)


class AddressForm(forms.ModelForm):
    """Standalone form for Address creation/editing with full map support"""

    class Meta:
        model = Address
        fields = [
            # Person association
            "hr_person",
            # Address type and purpose
            "hr_kind",
            "hr_use",
            "is_primary_hint",
            "label",
            "address_kind",
            # Core address fields
            "address_line1",
            "address_line2",
            "city",
            "state_region",
            "postal_code",
            "country_iso2",
            # Structured fields (Saudi National Address)
            "street_name",
            "building_number",
            "unit_number",
            "neighborhood",
            "additional_number",
            "po_box",
            # Geolocation
            "latitude",
            "longitude",
            # Notes
            "accessibility_notes",
        ]
        widgets = {
            "hr_person": forms.Select(attrs={"class": "form-select"}),
            "hr_kind": forms.Select(attrs={"class": "form-select"}),
            "hr_use": forms.Select(attrs={"class": "form-select"}),
            "is_primary_hint": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "label": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Home, Work, Main Office"}),
            "address_kind": forms.Select(attrs={"class": "form-select"}),
            "address_line1": forms.TextInput(attrs={"class": "form-control", "placeholder": "Street address, building, etc."}),
            "address_line2": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apartment, suite, unit (optional)"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "City or town"}),
            "state_region": forms.TextInput(attrs={"class": "form-control", "placeholder": "State, province, or region"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Postal/ZIP code"}),
            "country_iso2": forms.Select(attrs={"class": "form-select"}),
            "street_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Street name"}),
            "building_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Building number"}),
            "unit_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Unit/apartment number"}),
            "neighborhood": forms.TextInput(attrs={"class": "form-control", "placeholder": "Neighborhood/district"}),
            "additional_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "4-digit additional number"}),
            "po_box": forms.TextInput(attrs={"class": "form-control", "placeholder": "P.O. Box number"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001", "placeholder": "e.g., 24.713552"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001", "placeholder": "e.g., 46.675297"}),
            "accessibility_notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Notes about accessibility, parking, etc."}),
        }
        labels = {
            "hr_person": "Person",
            "hr_kind": "Address Type",
            "hr_use": "Usage Type",
            "is_primary_hint": "Set as Primary Address",
            "label": "Label",
            "address_kind": "Address Format",
            "address_line1": "Address Line 1",
            "address_line2": "Address Line 2",
            "city": "City",
            "state_region": "State/Province/Region",
            "postal_code": "Postal Code",
            "country_iso2": "Country",
            "street_name": "Street Name",
            "building_number": "Building Number",
            "unit_number": "Unit Number",
            "neighborhood": "Neighborhood",
            "additional_number": "Additional Number",
            "po_box": "P.O. Box",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "accessibility_notes": "Accessibility Notes",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make hr_person required
        self.fields["hr_person"].required = True
        self.fields["hr_person"].queryset = HRPeople.objects.filter(is_deleted=False).order_by("first_name_en", "last_name_en")
        self.fields["hr_person"].empty_label = "-- Select Person --"

        # Set empty labels for select fields
        self.fields["hr_kind"].empty_label = "-- Select Type --"
        self.fields["hr_use"].empty_label = "-- Select Usage --"
        self.fields["country_iso2"].empty_label = "-- Select Country --"

        # Make core fields required
        self.fields["address_line1"].required = True
        self.fields["country_iso2"].required = True
