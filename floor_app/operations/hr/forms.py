from django import forms
from django.forms import inlineformset_factory

from .models import HRPeople, HREmployee, HRPhone, HREmail, HRAddress


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
            "report_to",
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

HRAddressFormSet = inlineformset_factory(
    HRPeople,
    HRAddress,
    fields="__all__",
    exclude=("person", "created_at", "created_by", "updated_at", "updated_by", "is_deleted", "deleted_at"),
    extra=1,
    can_delete=True,
)
