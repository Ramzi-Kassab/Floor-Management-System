from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods
import json
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
            # Use atomic transaction for all saves
            try:
                with transaction.atomic():
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
            except Exception as e:
                messages.error(request, f'Error saving employee: {str(e)}')
                # Continue to show form with errors
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


# ============================================================================
# AJAX ENDPOINTS FOR PROGRESSIVE TAB SAVES
# ============================================================================

@login_required
@require_http_methods(["POST"])
def save_person_tab(request):
    """
    AJAX endpoint to save Person tab data individually.
    Returns JSON with success status and person ID.

    Handles duplicate national_id by offering to use existing person.
    """
    try:
        person_id = request.POST.get('person_id')
        national_id = request.POST.get('national_id', '').strip()
        person = None
        is_new = True

        if person_id:
            person = get_object_or_404(HRPeople, pk=person_id)
            is_new = False

        people_form = HRPeopleForm(request.POST, request.FILES, instance=person)

        if people_form.is_valid():
            with transaction.atomic():
                person_obj = people_form.save(commit=False)
                person_obj.updated_by = request.user
                if is_new:
                    person_obj.created_by = request.user
                person_obj.save()

            return JsonResponse({
                'success': True,
                'person_id': person_obj.pk,
                'full_name': person_obj.get_full_name_en(),
                'message': 'Person information saved successfully.'
            })
        else:
            # Return form errors
            errors = {}
            for field, error_list in people_form.errors.items():
                errors[field] = error_list
            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': 'Please fix the errors in the form.'
            }, status=400)
    except Exception as e:
        error_msg = str(e)

        # Check if it's a duplicate national_id error
        if 'uq_hr_people_national_id' in error_msg or 'duplicate key' in error_msg.lower():
            # Try to find existing person with this national_id
            if national_id:
                try:
                    existing_person = HRPeople.objects.get(national_id__iexact=national_id)
                    return JsonResponse({
                        'success': False,
                        'message': f'A Person with National ID "{national_id}" already exists. Using existing record.',
                        'person_id': existing_person.pk,
                        'full_name': existing_person.get_full_name_en(),
                        'existing_person': True
                    }, status=409)  # 409 Conflict
                except HRPeople.DoesNotExist:
                    pass

            return JsonResponse({
                'success': False,
                'message': f'A Person with this National ID already exists in the system. Please use the existing record or contact administration.'
            }, status=409)

        return JsonResponse({
            'success': False,
            'message': f'Error saving person data: {error_msg}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def save_employee_tab(request):
    """
    AJAX endpoint to save Employee tab data individually.
    Requires person_id to be provided.
    """
    try:
        person_id = request.POST.get('person_id')
        employee_id = request.POST.get('employee_id')

        if not person_id:
            return JsonResponse({
                'success': False,
                'message': 'Person must be created first. Please save Person tab.'
            }, status=400)

        person = get_object_or_404(HRPeople, pk=person_id)
        employee = None
        is_new = True

        if employee_id:
            employee = get_object_or_404(HREmployee, pk=employee_id)
            is_new = False

        employee_form = HREmployeeForm(request.POST, instance=employee)

        if employee_form.is_valid():
            with transaction.atomic():
                employee_obj = employee_form.save(commit=False)
                employee_obj.person = person
                employee_obj.updated_by = request.user
                if is_new:
                    employee_obj.created_by = request.user
                employee_obj.save()

            return JsonResponse({
                'success': True,
                'employee_id': employee_obj.pk,
                'message': 'Employee information saved successfully.'
            })
        else:
            errors = {}
            for field, error_list in employee_form.errors.items():
                errors[field] = list(error_list)

            # Build detailed error message
            error_msg = 'Validation errors in employee information:\n'
            for field, error_list in errors.items():
                field_label = employee_form.fields[field].label if field in employee_form.fields else field
                error_msg += f"  • {field_label}: {', '.join(error_list)}\n"

            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': error_msg.strip()
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving employee data: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def save_phones_tab(request):
    """
    AJAX endpoint to save Phones tab data individually.
    Requires person_id to be provided.
    """
    try:
        person_id = request.POST.get('person_id')

        if not person_id:
            return JsonResponse({
                'success': False,
                'message': 'Person must be created first. Please save Person tab.'
            }, status=400)

        person = get_object_or_404(HRPeople, pk=person_id)
        phone_formset = HRPhoneFormSet(request.POST, instance=person, prefix="phones")

        if phone_formset.is_valid():
            with transaction.atomic():
                for phone_form in phone_formset:
                    if phone_form.instance:
                        phone_form.instance.updated_by = request.user
                        if not phone_form.instance.pk:
                            phone_form.instance.created_by = request.user

                phone_formset.save()

            return JsonResponse({
                'success': True,
                'count': len([f for f in phone_formset if f.cleaned_data]),
                'message': 'Phone numbers saved successfully.'
            })
        else:
            # Return detailed formset errors
            errors = {}
            non_form_errors = phone_formset.non_form_errors()
            if non_form_errors:
                errors['__all__'] = list(non_form_errors)

            for i, form in enumerate(phone_formset):
                if form.errors:
                    errors[f'phone_{i}'] = {}
                    for field, error_list in form.errors.items():
                        errors[f'phone_{i}'][field] = list(error_list)

            error_msg = 'Validation errors in phone numbers:\n'
            for key, value in errors.items():
                if isinstance(value, dict):
                    for field, field_errors in value.items():
                        error_msg += f"  • {field}: {', '.join(field_errors)}\n"
                elif isinstance(value, list):
                    error_msg += f"  • {', '.join(value)}\n"

            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': error_msg.strip()
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving phone data: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def save_emails_tab(request):
    """
    AJAX endpoint to save Emails tab data individually.
    Requires person_id to be provided.
    """
    try:
        person_id = request.POST.get('person_id')

        if not person_id:
            return JsonResponse({
                'success': False,
                'message': 'Person must be created first. Please save Person tab.'
            }, status=400)

        person = get_object_or_404(HRPeople, pk=person_id)
        email_formset = HREmailFormSet(request.POST, instance=person, prefix="emails")

        if email_formset.is_valid():
            with transaction.atomic():
                for email_form in email_formset:
                    if email_form.instance:
                        email_form.instance.updated_by = request.user
                        if not email_form.instance.pk:
                            email_form.instance.created_by = request.user

                email_formset.save()

            return JsonResponse({
                'success': True,
                'count': len([f for f in email_formset if f.cleaned_data]),
                'message': 'Email addresses saved successfully.'
            })
        else:
            # Return detailed formset errors
            errors = {}
            non_form_errors = email_formset.non_form_errors()
            if non_form_errors:
                errors['__all__'] = list(non_form_errors)

            for i, form in enumerate(email_formset):
                if form.errors:
                    errors[f'email_{i}'] = {}
                    for field, error_list in form.errors.items():
                        errors[f'email_{i}'][field] = list(error_list)

            error_msg = 'Validation errors in email addresses:\n'
            for key, value in errors.items():
                if isinstance(value, dict):
                    for field, field_errors in value.items():
                        error_msg += f"  • {field}: {', '.join(field_errors)}\n"
                elif isinstance(value, list):
                    error_msg += f"  • {', '.join(value)}\n"

            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': error_msg.strip()
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving email data: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def save_addresses_tab(request):
    """
    AJAX endpoint to save Addresses tab data individually.
    Requires person_id to be provided.
    """
    try:
        person_id = request.POST.get('person_id')

        if not person_id:
            return JsonResponse({
                'success': False,
                'message': 'Person must be created first. Please save Person tab.'
            }, status=400)

        person = get_object_or_404(HRPeople, pk=person_id)
        address_formset = AddressFormSet(request.POST, instance=person, prefix="addresses")

        if address_formset.is_valid():
            with transaction.atomic():
                for address_form in address_formset:
                    if address_form.instance:
                        address_form.instance.updated_by = request.user
                        if not address_form.instance.pk:
                            address_form.instance.created_by = request.user

                address_formset.save()

            return JsonResponse({
                'success': True,
                'count': len([f for f in address_formset if f.cleaned_data]),
                'message': 'Addresses saved successfully.'
            })
        else:
            # Return detailed formset errors
            errors = {}
            non_form_errors = address_formset.non_form_errors()
            if non_form_errors:
                errors['__all__'] = list(non_form_errors)

            for i, form in enumerate(address_formset):
                if form.errors:
                    errors[f'address_{i}'] = {}
                    for field, error_list in form.errors.items():
                        errors[f'address_{i}'][field] = list(error_list)

            error_msg = 'Validation errors in addresses:\n'
            for key, value in errors.items():
                if isinstance(value, dict):
                    for field, field_errors in value.items():
                        error_msg += f"  • {field}: {', '.join(field_errors)}\n"
                elif isinstance(value, list):
                    error_msg += f"  • {', '.join(value)}\n"

            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': error_msg.strip()
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving address data: {str(e)}'
        }, status=500)


# ============================================================================
# PERSON LOOKUP AND MANAGEMENT ENDPOINTS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def person_list_api(request):
    """
    AJAX endpoint to get list of all persons for selection.
    Returns JSON array of persons.
    """
    try:
        # Get search query if provided
        search_query = request.GET.get('q', '').strip()

        # Start with all non-deleted persons
        queryset = HRPeople.objects.filter(is_deleted=False).order_by('-created_at')

        # Filter by search query
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name_en__icontains=search_query) |
                Q(last_name_en__icontains=search_query) |
                Q(national_id__icontains=search_query) |
                Q(iqama_number__icontains=search_query)
            )

        # Limit results
        persons = queryset[:50]

        # Format response
        data = {
            'success': True,
            'persons': [
                {
                    'id': person.pk,
                    'name': person.get_full_name_en(),
                    'national_id': person.national_id,
                    'iqama_number': person.iqama_number,
                    'gender': person.get_gender_display() if hasattr(person, 'get_gender_display') else person.gender,
                    'created_at': person.created_at.strftime('%Y-%m-%d %H:%M'),
                }
                for person in persons
            ]
        }

        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching persons: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def person_detail_api(request, person_id):
    """
    AJAX endpoint to get person details with related data.
    """
    try:
        person = get_object_or_404(HRPeople, pk=person_id)

        return JsonResponse({
            'success': True,
            'person': {
                'id': person.pk,
                'first_name_en': person.first_name_en,
                'middle_name_en': person.middle_name_en,
                'last_name_en': person.last_name_en,
                'first_name_ar': person.first_name_ar,
                'middle_name_ar': person.middle_name_ar,
                'last_name_ar': person.last_name_ar,
                'gender': person.gender,
                'date_of_birth': person.date_of_birth.isoformat() if person.date_of_birth else None,
                'date_of_birth_hijri': person.date_of_birth_hijri,
                'primary_nationality_iso2': person.primary_nationality_iso2,
                'national_id': person.national_id,
                'iqama_number': person.iqama_number,
                'iqama_expiry': person.iqama_expiry.isoformat() if person.iqama_expiry else None,
                'phones': [
                    {
                        'id': phone.pk,
                        'country_iso2': phone.country_iso2,
                        'phone_number': phone.phone_number,
                        'kind': phone.kind,
                        'use': phone.use,
                    }
                    for phone in person.phones.filter(is_deleted=False)
                ],
                'emails': [
                    {
                        'id': email.pk,
                        'email': email.email,
                        'kind': email.kind,
                    }
                    for email in person.emails.filter(is_deleted=False)
                ],
                'addresses': [
                    {
                        'id': address.pk,
                        'address_line1': address.address_line1,
                        'city': address.city,
                        'country_iso2': address.country_iso2,
                    }
                    for address in person.addresses.filter(is_deleted=False)
                ],
                'created_at': person.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': person.updated_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching person details: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def phones_list_api(request):
    """
    API endpoint to get all phones with person details.
    Returns a list of phones showing phone number, person name, kind, use, etc.
    """
    try:
        from .models import HRPhone

        # Get search query if provided
        search_q = request.GET.get('q', '').strip()

        # Get all phones with person info
        phones = HRPhone.objects.filter(is_deleted=False).select_related('person').order_by('-created_at')

        # Filter by search query (phone number or person name)
        if search_q:
            from django.db.models import Q
            phones = phones.filter(
                Q(phone_e164__icontains=search_q) |
                Q(person__first_name_en__icontains=search_q) |
                Q(person__last_name_en__icontains=search_q) |
                Q(person__first_name_ar__icontains=search_q) |
                Q(person__last_name_ar__icontains=search_q)
            )

        # Limit results
        phones = phones[:100]

        phones_data = []
        for phone in phones:
            person_name = f"{phone.person.first_name_en} {phone.person.last_name_en}".strip() if phone.person else "No Person"
            phones_data.append({
                'id': phone.id,
                'phone_number': str(phone),
                'phone_e164': phone.phone_e164,
                'person_id': phone.person.id if phone.person else None,
                'person_name': person_name,
                'kind': phone.get_kind_display(),
                'use': phone.get_use_display(),
                'channel': phone.get_channel_display(),
                'country': phone.country_iso2,
                'is_primary': phone.is_primary_hint,
                'created_at': phone.created_at.strftime('%Y-%m-%d %H:%M'),
            })

        return JsonResponse({
            'success': True,
            'phones': phones_data,
            'count': len(phones_data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching phones list: {str(e)}'
        }, status=500)