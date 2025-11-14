from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import HREmployee, HRPeople
from .forms import (
    HRPeopleForm,
    HREmployeeForm,
    HRPhoneFormSet,
    HREmailFormSet,
    AddressFormSet,
)


def _render_employee_form(request, employee=None, person=None, is_new=True, template_name="hr/employee_create.html"):
    """
    Helper function to handle employee form rendering for both create and edit views.
    """
    if request.method == "POST":
        # include FILES for the photo field
        people_form = HRPeopleForm(request.POST, request.FILES, instance=person)
        employee_form = HREmployeeForm(request.POST, instance=employee)

        if people_form.is_valid() and employee_form.is_valid():
            # Save person with audit tracking
            person_obj = people_form.save(commit=False)
            person_obj.updated_by = request.user
            if is_new:
                person_obj.created_by = request.user
            person_obj.save()

            # Save employee with audit tracking
            employee_obj = employee_form.save(commit=False)
            employee_obj.person = person_obj
            employee_obj.updated_by = request.user
            if is_new:
                employee_obj.created_by = request.user
            employee_obj.save()

            phone_formset = HRPhoneFormSet(
                request.POST, instance=person_obj, prefix="phones"
            )
            email_formset = HREmailFormSet(
                request.POST, instance=person_obj, prefix="emails"
            )
            address_formset = AddressFormSet(
                request.POST, instance=person_obj, prefix="addresses"
            )

            if (
                phone_formset.is_valid()
                and email_formset.is_valid()
                and address_formset.is_valid()
            ):
                # Save formsets with audit tracking
                for phone_form in phone_formset:
                    if phone_form.instance:
                        phone_form.instance.updated_by = request.user
                        if not phone_form.instance.pk:
                            phone_form.instance.created_by = request.user

                for email_form in email_formset:
                    if email_form.instance:
                        email_form.instance.updated_by = request.user
                        if not email_form.instance.pk:
                            email_form.instance.created_by = request.user

                for address_form in address_formset:
                    if address_form.instance:
                        address_form.instance.updated_by = request.user
                        if not address_form.instance.pk:
                            address_form.instance.created_by = request.user

                phone_formset.save()
                email_formset.save()
                address_formset.save()

                action = "created" if is_new else "updated"
                messages.success(request, f'Employee "{person_obj.get_full_name_en()}" has been {action} successfully.')
                return redirect("employee_detail", pk=employee_obj.pk)
        else:
            phone_formset = HRPhoneFormSet(request.POST, instance=person, prefix="phones")
            email_formset = HREmailFormSet(request.POST, instance=person, prefix="emails")
            address_formset = AddressFormSet(
                request.POST, instance=person, prefix="addresses"
            )

    else:  # GET
        people_form = HRPeopleForm(instance=person)
        employee_form = HREmployeeForm(instance=employee)
        phone_formset = HRPhoneFormSet(instance=person, prefix="phones")
        email_formset = HREmailFormSet(instance=person, prefix="emails")
        address_formset = AddressFormSet(instance=person, prefix="addresses")

    context = {
        "employee": employee,
        "is_new": is_new,
        "people_form": people_form,
        "employee_form": employee_form,
        "phone_formset": phone_formset,
        "email_formset": email_formset,
        "address_formset": address_formset,
    }
    return render(request, template_name, context)


@login_required
def employee_create(request):
    """
    Create a new employee record with personal information and contact details.
    """
    person = HRPeople()
    employee = None
    return _render_employee_form(
        request,
        employee=employee,
        person=person,
        is_new=True,
        template_name="hr/employee_create.html"
    )


@login_required
def employee_edit(request, pk):
    """
    Edit an existing employee record with personal information and contact details.
    """
    employee = get_object_or_404(HREmployee, pk=pk)
    person = employee.person
    return _render_employee_form(
        request,
        employee=employee,
        person=person,
        is_new=False,
        template_name="hr/employee_edit.html"
    )


@login_required
def employee_setup(request, employee_id=None):
    """
    DEPRECATED: Use employee_create() or employee_edit() instead.
    Kept for backward compatibility during transition.
    """
    if employee_id:
        return redirect("hr:employee_edit", pk=employee_id)
    else:
        return redirect("hr:employee_create")


@login_required
def employee_setup_list(request):
    """
    DEPRECATED: Use employee_list view instead.
    Kept for backward compatibility during transition.
    """
    return redirect("employee_list")