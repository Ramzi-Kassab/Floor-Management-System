from django import forms
from django.forms import inlineformset_factory

from .models import HRPeople, HREmployee, HRPhone, HREmail, HRAddress


class HRPeopleForm(forms.ModelForm):
    class Meta:
        model = HRPeople
        exclude = (
            "public_id",
            "created_at", "created_by",
            "updated_at", "updated_by",
            "is_deleted", "deleted_at",
        )


class HREmployeeForm(forms.ModelForm):
    class Meta:
        model = HREmployee
        fields = [
            "user",
            "employee_no",
            "status",
            "job_title",
            "team",
            "is_operator",
            "hire_date",
            "termination_date",
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
