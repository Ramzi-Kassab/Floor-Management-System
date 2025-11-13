from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import HREmployee, HRPeople
from .forms import (
    HRPeopleForm,
    HREmployeeForm,
    HRPhoneFormSet,
    HREmailFormSet,
    HRAddressFormSet,
)

def employee_setup(request, employee_id=None):
    if employee_id:
        employee = get_object_or_404(HREmployee, pk=employee_id)
        person = employee.person
        is_new = False
    else:
        employee = None
        person = HRPeople()  # empty instance
        is_new = True

    if request.method == "POST":
        # include FILES for the photo field
        people_form = HRPeopleForm(request.POST, request.FILES, instance=person)
        employee_form = HREmployeeForm(request.POST, instance=employee)

        if people_form.is_valid() and employee_form.is_valid():
            person_obj = people_form.save()

            employee_obj = employee_form.save(commit=False)
            employee_obj.person = person_obj
            employee_obj.save()

            phone_formset = HRPhoneFormSet(
                request.POST, instance=person_obj, prefix="phones"
            )
            email_formset = HREmailFormSet(
                request.POST, instance=person_obj, prefix="emails"
            )
            address_formset = HRAddressFormSet(
                request.POST, instance=person_obj, prefix="addresses"
            )

            if (
                phone_formset.is_valid()
                and email_formset.is_valid()
                and address_formset.is_valid()
            ):
                phone_formset.save()
                email_formset.save()
                address_formset.save()

                return redirect("hr_employee_setup", employee_id=employee_obj.pk)
        else:
            phone_formset = HRPhoneFormSet(request.POST, instance=person, prefix="phones")
            email_formset = HREmailFormSet(request.POST, instance=person, prefix="emails")
            address_formset = HRAddressFormSet(
                request.POST, instance=person, prefix="addresses"
            )

    else:  # GET
        people_form = HRPeopleForm(instance=person)
        employee_form = HREmployeeForm(instance=employee)
        phone_formset = HRPhoneFormSet(instance=person, prefix="phones")
        email_formset = HREmailFormSet(instance=person, prefix="emails")
        address_formset = HRAddressFormSet(instance=person, prefix="addresses")

    # 🔹 these are what the template needs for the buttons
    admin_list_url = reverse("admin:floor_app_hremployee_changelist")
    admin_change_url = (
        reverse("admin:floor_app_hremployee_change", args=[employee.pk])
        if employee
        else None
    )

    context = {
        "employee": employee,
        "is_new": is_new,
        "people_form": people_form,
        "employee_form": employee_form,
        "phone_formset": phone_formset,
        "email_formset": email_formset,
        "address_formset": address_formset,
        "admin_list_url": admin_list_url,
        "admin_change_url": admin_change_url,
    }
    return render(request, "hr/employee_setup.html", context)

@login_required
def employee_setup_list(request):
    """
    Entry point for the Employee Setup menu item.
    For now this simply redirects to the 'new' setup wizard.
    Later you can replace this with a proper list of employees, if you like.
    """
    return redirect("hr:employee_setup_new")