# views_employee_wizard.py
# New wizard-based employee creation system

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
import json
from datetime import datetime

from floor_app.operations.hr.models import (
    HRPeople, HREmployee, HRPhone, HREmail,
    Department, Position, Address
)
from floor_app.operations.hr.forms import (
    HRPeopleForm, HREmployeeForm, HRPhoneFormSet,
    HREmailFormSet, AddressFormSet, AddressForm
)


# ========== HR Dashboard ==========
@login_required
def hr_dashboard(request):
    """Main HR & Administration dashboard"""
    context = {
        # Employees – these models have is_deleted
        'total_employees': HREmployee.objects.filter(is_deleted=False).count(),
        'active_employees': HREmployee.objects.filter(
            is_deleted=False,
            status='ACTIVE'
        ).count(),

        # Departments – no soft delete / is_active fields yet
        'departments_count': Department.objects.count(),
        'active_departments': Department.objects.count(),  # treat all as active for now

        # Positions – uses HRSoftDeleteMixin, so is_deleted is OK
        'positions_count': Position.objects.filter(is_deleted=False).count(),
        'filled_positions': Position.objects.filter(
            is_deleted=False
        ).exclude(employees=None).count(),

        # People & contacts – all have is_deleted
        'people_count': HRPeople.objects.filter(is_deleted=False).count(),
        'phones_count': HRPhone.objects.filter(is_deleted=False).count(),
        'emails_count': HREmail.objects.filter(is_deleted=False).count(),

        # Addresses – NO content_type anymore, just count non-deleted
        'addresses_count': Address.objects.filter(is_deleted=False).count(),
    }
    return render(request, 'hr/hr_dashboard.html', context)


@login_required
def dashboard_stats(request):
    """API endpoint for dashboard statistics (for auto-refresh)"""
    stats = {
        'total_employees': HREmployee.objects.filter(is_deleted=False).count(),
        'active_employees': HREmployee.objects.filter(
            is_deleted=False,
            status='ACTIVE'
        ).count(),
        'on_leave': HREmployee.objects.filter(
            is_deleted=False,
            status='ON_LEAVE'
        ).count(),
    }
    return JsonResponse(stats)


# ========== Employee Creation Wizard ==========
@login_required
def employee_wizard_start(request):
    """Step 1: Person selection or creation"""
    return render(request, 'hr/employee_wizard_person.html')


@login_required
def employee_wizard_contact(request):
    """Step 2: Contact information (phones, emails, addresses)"""
    return render(request, 'hr/employee_wizard_contact.html')


@login_required
def employee_wizard_employee(request):
    """Step 3: Employee details"""
    return render(request, 'hr/employee_wizard_employee.html')


@login_required
def employee_wizard_review(request):
    """Step 4: Review and save"""
    return render(request, 'hr/employee_wizard_review.html')


# ========== Person Management ==========
@login_required
def people_list(request):
    """List all people with filtering and pagination"""
    queryset = HRPeople.objects.filter(is_deleted=False)
    
    # Search filters
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(first_name_en__icontains=search) |
            Q(last_name_en__icontains=search) |
            Q(national_id__icontains=search) |
            Q(iqama_number__icontains=search)
        )
    
    # Nationality filter
    nationality = request.GET.get('nationality')
    if nationality:
        queryset = queryset.filter(primary_nationality_iso2=nationality)
    
    # Gender filter
    gender = request.GET.get('gender')
    if gender:
        queryset = queryset.filter(gender=gender)
    
    # Verification status filter
    verified = request.GET.get('verified')
    if verified == 'yes':
        queryset = queryset.filter(identity_verified=True)
    elif verified == 'no':
        queryset = queryset.filter(identity_verified=False)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    queryset = queryset.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(queryset, 25)
    page = request.GET.get('page')
    people = paginator.get_page(page)
    
    context = {
        'people': people,
        'search': search,
        'total_count': queryset.count(),
    }
    return render(request, 'hr/people_list.html', context)


@login_required
def person_create(request):
    """Create a new person"""
    if request.method == 'POST':
        form = HRPeopleForm(request.POST, request.FILES)
        if form.is_valid():
            person = form.save(commit=False)
            person.created_by = request.user
            person.save()
            messages.success(request, f'Person {person.get_full_name_en()} created successfully.')
            return redirect('hr:person_detail', pk=person.id)
    else:
        form = HRPeopleForm()
    
    return render(request, 'hr/person_form.html', {'form': form, 'title': 'Create Person'})


@login_required
def person_detail(request, pk):
    """View person details"""
    person = get_object_or_404(HRPeople, pk=pk, is_deleted=False)
    
    context = {
        'person': person,
        'phones': person.phones.filter(is_deleted=False),
        'emails': person.emails.filter(is_deleted=False),
        'addresses': Address.objects.filter(
            content_type__model='hrpeople',
            object_id=person.id,
            is_deleted=False
        ),
        'has_employee': hasattr(person, 'employee'),
    }
    return render(request, 'hr/person_detail.html', context)


@login_required
def person_edit(request, pk):
    """Edit person details"""
    person = get_object_or_404(HRPeople, pk=pk, is_deleted=False)
    
    if request.method == 'POST':
        form = HRPeopleForm(request.POST, request.FILES, instance=person)
        if form.is_valid():
            person = form.save(commit=False)
            person.updated_by = request.user
            person.save()
            messages.success(request, 'Person updated successfully.')
            return redirect('hr:person_detail', pk=person.id)
    else:
        form = HRPeopleForm(instance=person)
    
    return render(request, 'hr/person_form.html', {
        'form': form,
        'title': 'Edit Person',
        'person': person
    })


@login_required
def person_delete(request, pk):
    """Soft delete a person"""
    person = get_object_or_404(HRPeople, pk=pk, is_deleted=False)
    
    if request.method == 'POST':
        person.is_deleted = True
        person.deleted_at = datetime.now()
        person.deleted_by = request.user
        person.save()
        messages.success(request, 'Person deleted successfully.')
        return redirect('hr:people_list')
    
    return render(request, 'hr/confirm_delete.html', {
        'object': person,
        'object_type': 'Person'
    })


# ========== AJAX APIs for Wizard ==========
@login_required
def person_search_api(request):
    """API to search for existing people"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    data = json.loads(request.body)
    national_id = data.get('national_id', '')
    iqama_number = data.get('iqama_number', '')
    
    queryset = HRPeople.objects.filter(is_deleted=False)
    
    if national_id:
        queryset = queryset.filter(national_id__icontains=national_id)
    if iqama_number:
        queryset = queryset.filter(iqama_number__icontains=iqama_number)
    
    results = []
    for person in queryset[:10]:  # Limit to 10 results
        results.append({
            'id': person.id,
            'full_name_en': person.get_full_name_en(),
            'full_name_ar': f"{person.first_name_ar} {person.last_name_ar}".strip() if person.first_name_ar else None,
            'national_id': person.national_id,
            'iqama_number': person.iqama_number,
            'nationality_display': person.get_primary_nationality_iso2_display(),
            'date_of_birth': person.date_of_birth.isoformat() if person.date_of_birth else None,
            'photo': person.photo.url if person.photo else None,
            'has_employee': hasattr(person, 'employee'),
        })
    
    return JsonResponse({'results': results})


@login_required
def person_detail_api(request, person_id):
    """API to get person details"""
    person = get_object_or_404(HRPeople, pk=person_id, is_deleted=False)
    
    data = {
        'id': person.id,
        'full_name_en': person.get_full_name_en(),
        'first_name_en': person.first_name_en,
        'middle_name_en': person.middle_name_en,
        'last_name_en': person.last_name_en,
        'first_name_ar': person.first_name_ar,
        'middle_name_ar': person.middle_name_ar,
        'last_name_ar': person.last_name_ar,
        'national_id': person.national_id,
        'iqama_number': person.iqama_number,
        'iqama_expiry': person.iqama_expiry.isoformat() if person.iqama_expiry else None,
        'date_of_birth': person.date_of_birth.isoformat() if person.date_of_birth else None,
        'date_of_birth_hijri': person.date_of_birth_hijri,
        'gender': person.gender,
        'marital_status': person.marital_status,
        'nationality_display': person.get_primary_nationality_iso2_display(),
        'primary_nationality_iso2': person.primary_nationality_iso2,
        'photo': person.photo.url if person.photo else None,
        'identity_verified': person.identity_verified,
    }
    
    return JsonResponse(data)


@login_required
@transaction.atomic
def person_create_ajax(request):
    """AJAX endpoint to create a new person"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        form = HRPeopleForm(request.POST, request.FILES)
        
        if form.is_valid():
            person = form.save(commit=False)
            person.created_by = request.user
            person.save()
            
            return JsonResponse({
                'success': True,
                'person_id': person.id,
                'message': 'Person created successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': str(e)
        }, status=400)


@login_required
def person_contacts_api(request, person_id):
    """API to get all contacts for a person"""
    person = get_object_or_404(HRPeople, pk=person_id, is_deleted=False)
    
    # Get phones
    phones = []
    for phone in person.phones.filter(is_deleted=False):
        phones.append({
            'id': phone.id,
            'country_iso2': phone.country_iso2,
            'calling_code': phone.calling_code,
            'phone_number': phone.phone_number,
            'phone_e164': phone.phone_e164,
            'channel': phone.channel,
            'kind': phone.kind,
            'use': phone.use,
            'extension': phone.extension,
            'is_primary_hint': phone.is_primary_hint,
            'label': phone.label,
        })
    
    # Get emails
    emails = []
    for email in person.emails.filter(is_deleted=False):
        emails.append({
            'id': email.id,
            'email': email.email,
            'kind': email.kind,
            'is_primary_hint': email.is_primary_hint,
            'label': email.label,
            'is_verified': email.is_verified,
        })
    
    # Get addresses
    addresses = []
    for address in Address.objects.filter(
        content_type__model='hrpeople',
        object_id=person.id,
        is_deleted=False
    ):
        addresses.append({
            'id': address.id,
            'building_number': address.building_number,
            'street_name': address.street_name,
            'district': address.district,
            'city': address.city,
            'postal_code': address.postal_code,
            'additional_number': address.additional_number,
            'unit': address.unit,
            'latitude': str(address.latitude) if address.latitude else None,
            'longitude': str(address.longitude) if address.longitude else None,
            'type': address.type,
            'label': address.label,
            'is_primary': address.is_primary,
        })
    
    return JsonResponse({
        'phones': phones,
        'emails': emails,
        'addresses': addresses,
    })


@login_required
@transaction.atomic
def save_contacts_ajax(request):
    """AJAX endpoint to save contact information"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        person_id = data.get('person_id')
        
        if not person_id:
            return JsonResponse({'success': False, 'errors': 'Person ID required'})
        
        person = get_object_or_404(HRPeople, pk=person_id, is_deleted=False)
        
        # Save phones
        for phone_data in data.get('phones', []):
            if 'id' not in phone_data:  # New phone
                phone = HRPhone(
                    person=person,
                    country_iso2=phone_data.get('country_iso2'),
                    calling_code=phone_data.get('calling_code'),
                    phone_number=phone_data.get('phone_number'),
                    channel=phone_data.get('channel', 'CALL'),
                    kind=phone_data.get('kind', 'MOBILE'),
                    use=phone_data.get('use', 'PERSONAL'),
                    is_primary_hint=phone_data.get('is_primary_hint', False),
                    label=phone_data.get('label', ''),
                    created_by=request.user
                )
                phone.clean()  # Validate
                phone.save()
        
        # Save emails
        for email_data in data.get('emails', []):
            if 'id' not in email_data:  # New email
                email = HREmail(
                    person=person,
                    email=email_data.get('email'),
                    kind=email_data.get('kind', 'PERSONAL'),
                    is_primary_hint=email_data.get('is_primary_hint', False),
                    label=email_data.get('label', ''),
                    created_by=request.user
                )
                email.clean()  # Validate
                email.save()
        
        # Save addresses
        from django.contrib.contenttypes.models import ContentType
        person_ct = ContentType.objects.get_for_model(HRPeople)
        
        for address_data in data.get('addresses', []):
            if 'id' not in address_data:  # New address
                address = Address(
                    content_type=person_ct,
                    object_id=person.id,
                    building_number=address_data.get('building_number', ''),
                    street_name=address_data.get('street_name', ''),
                    district=address_data.get('district', ''),
                    city=address_data.get('city', ''),
                    postal_code=address_data.get('postal_code', ''),
                    additional_number=address_data.get('additional_number', ''),
                    unit=address_data.get('unit', ''),
                    latitude=address_data.get('latitude'),
                    longitude=address_data.get('longitude'),
                    type=address_data.get('type', 'HOME'),
                    label=address_data.get('label', ''),
                    is_primary=address_data.get('is_primary', False),
                    created_by=request.user
                )
                address.save()
        
        return JsonResponse({'success': True, 'message': 'Contacts saved successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)}, status=400)


@login_required
def convert_date(request):
    """API to convert between Gregorian and Hijri dates"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from hijri_converter import Gregorian
        data = json.loads(request.body)
        gregorian_date = data.get('gregorian_date')
        
        if gregorian_date:
            year, month, day = map(int, gregorian_date.split('-'))
            hijri = Gregorian(year, month, day).to_hijri()
            hijri_date = f"{hijri.year:04d}-{hijri.month:02d}-{hijri.day:02d}"
            
            return JsonResponse({'hijri_date': hijri_date})
    except:
        pass
    
    return JsonResponse({'hijri_date': ''})


# ========== Employee Management ==========
@login_required
def employee_list(request):
    """List all employees with filtering"""
    queryset = HREmployee.objects.filter(is_deleted=False).select_related(
        'person', 'department', 'position'
    )
    
    # Search filter
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(employee_no__icontains=search) |
            Q(person__first_name_en__icontains=search) |
            Q(person__last_name_en__icontains=search) |
            Q(person__national_id__icontains=search)
        )
    
    # Department filter
    department = request.GET.get('department')
    if department:
        queryset = queryset.filter(department_id=department)
    
    # Status filter
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)
    
    # Contract type filter
    contract_type = request.GET.get('contract_type')
    if contract_type:
        queryset = queryset.filter(contract_type=contract_type)
    
    # Sorting
    sort_by = request.GET.get('sort', 'employee_no')
    queryset = queryset.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(queryset, 25)
    page = request.GET.get('page')
    employees = paginator.get_page(page)
    
    context = {
        'employees': employees,
        'search': search,
        'departments': Department.objects.all(),
        'total_count': queryset.count(),
    }
    return render(request, 'hr/employee_list.html', context)


@login_required
def employee_active(request):
    """List active employees only"""
    queryset = HREmployee.objects.filter(
        is_deleted=False,
        status='ACTIVE'
    ).select_related('person', 'department', 'position')
    
    paginator = Paginator(queryset, 25)
    page = request.GET.get('page')
    employees = paginator.get_page(page)
    
    context = {
        'employees': employees,
        'title': 'Active Employees',
        'total_count': queryset.count(),
    }
    return render(request, 'hr/employee_list.html', context)


@login_required
def employee_detail(request, pk):
    """View employee details"""
    employee = get_object_or_404(
        HREmployee.objects.select_related('person', 'department', 'position'),
        pk=pk,
        is_deleted=False
    )

    context = {
        'employee': employee,
        'person': employee.person,
        'phones': employee.person.phones.filter(is_deleted=False),
        'emails': employee.person.emails.filter(is_deleted=False),
        'addresses': Address.objects.filter(
            content_type__model='hrpeople',
            object_id=employee.person.id,
            is_deleted=False
        ),
    }
    return render(request, 'hr/employee_detail.html', context)


@login_required
def employee_edit(request, pk):
    """Edit employee details"""
    employee = get_object_or_404(
        HREmployee.objects.select_related('person', 'department', 'position'),
        pk=pk,
        is_deleted=False
    )

    if request.method == 'POST':
        form = HREmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.updated_by = request.user
            employee.save()
            messages.success(request, f'Employee {employee.person.get_full_name_en()} updated successfully.')
            return redirect('hr:employee_detail', pk=employee.pk)
    else:
        form = HREmployeeForm(instance=employee)

    context = {
        'form': form,
        'employee': employee,
        'person': employee.person,
        'title': 'Edit Employee',
        'departments': Department.objects.all().order_by('name'),
        'positions': Position.objects.filter(is_deleted=False).order_by('name'),
    }
    return render(request, 'hr/employee_form.html', context)


@login_required
@transaction.atomic
def save_employee_ajax(request):
    """AJAX endpoint to save employee details"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        person_id = data.get('person_id')
        
        if not person_id:
            return JsonResponse({'success': False, 'errors': 'Person ID required'})
        
        person = get_object_or_404(HRPeople, pk=person_id, is_deleted=False)
        
        # Check if employee already exists
        if hasattr(person, 'employee'):
            employee = person.employee
        else:
            employee = HREmployee(person=person)
        
        # Update employee fields
        employee.employee_no = data.get('employee_no')
        employee.status = data.get('status', 'ACTIVE')
        employee.contract_type = data.get('contract_type', 'PERMANENT')
        employee.employment_status = data.get('employment_status', 'ACTIVE')
        employee.employment_category = data.get('employment_category', 'REGULAR')
        
        # Department and position
        if data.get('department_id'):
            employee.department_id = data.get('department_id')
        if data.get('position_id'):
            employee.position_id = data.get('position_id')
        
        # Dates
        if data.get('hire_date'):
            employee.hire_date = data.get('hire_date')
        if data.get('contract_start_date'):
            employee.contract_start_date = data.get('contract_start_date')
        if data.get('contract_end_date'):
            employee.contract_end_date = data.get('contract_end_date')
        if data.get('probation_end_date'):
            employee.probation_end_date = data.get('probation_end_date')
        
        # Work schedule
        employee.work_days_per_week = data.get('work_days_per_week', 5)
        employee.hours_per_week = data.get('hours_per_week', 40)
        employee.shift_pattern = data.get('shift_pattern', 'DAY')
        
        # Compensation
        if data.get('monthly_salary'):
            employee.monthly_salary = data.get('monthly_salary')
        employee.salary_grade = data.get('salary_grade', '')
        employee.benefits_eligible = data.get('benefits_eligible', True)
        employee.overtime_eligible = data.get('overtime_eligible', True)
        
        # Leave entitlements
        employee.annual_leave_days = data.get('annual_leave_days', 20)
        employee.sick_leave_days = data.get('sick_leave_days', 10)
        employee.special_leave_days = data.get('special_leave_days', 3)
        
        # Supervisor
        if data.get('report_to_id'):
            employee.report_to_id = data.get('report_to_id')
        
        employee.cost_center = data.get('cost_center', '')
        
        if not employee.pk:
            employee.created_by = request.user
        else:
            employee.updated_by = request.user
        
        employee.save()
        
        return JsonResponse({
            'success': True,
            'employee_id': employee.id,
            'message': 'Employee saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)}, status=400)


# ========== Import/Export Functions ==========
@login_required
def employee_import(request):
    """Import employees from CSV/Excel"""
    if request.method == 'POST' and request.FILES.get('file'):
        import pandas as pd
        
        try:
            file = request.FILES['file']
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Process the dataframe and create employees
            created_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Create or find person
                    person, _ = HRPeople.objects.get_or_create(
                        national_id=row['national_id'],
                        defaults={
                            'first_name_en': row['first_name_en'],
                            'last_name_en': row['last_name_en'],
                            'primary_nationality_iso2': row.get('nationality', 'SA'),
                            'gender': row.get('gender', 'MALE'),
                            'created_by': request.user
                        }
                    )
                    
                    # Create employee
                    employee, created = HREmployee.objects.get_or_create(
                        employee_no=row['employee_no'],
                        defaults={
                            'person': person,
                            'status': row.get('status', 'ACTIVE'),
                            'contract_type': row.get('contract_type', 'PERMANENT'),
                            'created_by': request.user
                        }
                    )
                    
                    if created:
                        created_count += 1
                        
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            if errors:
                messages.warning(request, f"Import completed with {len(errors)} errors.")
            else:
                messages.success(request, f"Successfully imported {created_count} employees.")
                
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
        
        return redirect('hr:employee_list')
    
    return render(request, 'hr/employee_import.html')


@login_required
def employee_export(request):
    """Export employees to CSV/Excel"""
    import pandas as pd
    from django.http import HttpResponse
    
    format = request.GET.get('format', 'excel')
    
    # Get employees
    employees = HREmployee.objects.filter(
        is_deleted=False
    ).select_related('person', 'department', 'position')
    
    # Prepare data
    data = []
    for emp in employees:
        data.append({
            'Employee No': emp.employee_no,
            'First Name': emp.person.first_name_en,
            'Middle Name': emp.person.middle_name_en,
            'Last Name': emp.person.last_name_en,
            'National ID': emp.person.national_id,
            'Iqama': emp.person.iqama_number,
            'Department': emp.department.name if emp.department else '',
            'Position': emp.position.title if emp.position else '',
            'Status': emp.status,
            'Contract Type': emp.contract_type,
            'Hire Date': emp.hire_date,
            'Email': emp.emails.filter(is_primary_hint=True).first().email if emp.emails.filter(is_primary_hint=True).exists() else '',
            'Phone': emp.phones.filter(is_primary_hint=True).first().phone_e164 if emp.phones.filter(is_primary_hint=True).exists() else '',
        })
    
    df = pd.DataFrame(data)
    
    # Generate response
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employees.csv"'
        df.to_csv(response, index=False)
    else:
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="employees.xlsx"'
        df.to_excel(response, index=False)
    
    return response


# ========== Phone Management ==========
@login_required
def phone_list(request):
    """List all phone numbers"""
    queryset = HRPhone.objects.filter(is_deleted=False).select_related('person')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(phone_e164__icontains=search) |
            Q(person__first_name_en__icontains=search) |
            Q(person__last_name_en__icontains=search)
        )
    
    paginator = Paginator(queryset, 25)
    page = request.GET.get('page')
    phones = paginator.get_page(page)
    
    context = {
        'phones': phones,
        'search': search,
        'total_count': queryset.count(),
    }
    return render(request, 'hr/phone_list.html', context)


@login_required
def phone_bulk_add(request):
    """Bulk add phone numbers"""
    if request.method == 'POST':
        # Handle bulk phone addition
        pass
    
    return render(request, 'hr/phone_bulk_add.html')


# ========== Email Management ==========
@login_required
def email_list(request):
    """List all email addresses"""
    queryset = HREmail.objects.filter(is_deleted=False).select_related('person')
    
    # Search
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(email__icontains=search) |
            Q(person__first_name_en__icontains=search) |
            Q(person__last_name_en__icontains=search)
        )
    
    paginator = Paginator(queryset, 25)
    page = request.GET.get('page')
    emails = paginator.get_page(page)
    
    context = {
        'emails': emails,
        'search': search,
        'total_count': queryset.count(),
    }
    return render(request, 'hr/email_list.html', context)


@login_required
def email_bulk_add(request):
    """Bulk add email addresses"""
    if request.method == 'POST':
        # Handle bulk email addition
        pass
    
    return render(request, 'hr/email_bulk_add.html')


# ========== Address Management ==========
@login_required
def address_list(request):
    """List all addresses for HR People"""
    # Query addresses using hr_person ForeignKey (not ContentType)
    queryset = Address.objects.filter(
        is_deleted=False,
        hr_person__isnull=False,
        hr_person__is_deleted=False
    ).select_related('hr_person', 'hr_person__employee').order_by('-created_at')

    # Search by city, district, street, or person name
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(city__icontains=search) |
            Q(district__icontains=search) |
            Q(street_name__icontains=search) |
            Q(country_iso2__icontains=search) |
            Q(hr_person__first_name_en__icontains=search) |
            Q(hr_person__last_name_en__icontains=search) |
            Q(hr_person__national_id__icontains=search)
        )

    # Filter by address type (label field)
    address_type = request.GET.get('type', '')
    if address_type:
        queryset = queryset.filter(label__iexact=address_type)

    # Get statistics
    total_count = queryset.count()

    # Add person alias for template compatibility
    addresses_list = []
    for address in queryset:
        address.person = address.hr_person  # Template expects 'person'
        addresses_list.append(address)

    paginator = Paginator(addresses_list, 25)
    page = request.GET.get('page')
    addresses = paginator.get_page(page)

    context = {
        'addresses': addresses,
        'search': search,
        'address_type': address_type,
        'total_count': total_count,
        'people': HRPeople.objects.filter(is_deleted=False).order_by('first_name_en'),
    }
    return render(request, 'hr/address_list.html', context)


@login_required
def address_add(request):
    """Add new address with map integration"""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.created_by = request.user
            address.updated_by = request.user
            address.save()
            messages.success(request, f'Address added successfully for {address.hr_person.get_full_name_en}.')
            return redirect('hr:address_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm()

    context = {
        'form': form,
        'address': None,
    }
    return render(request, 'hr/address_form.html', context)


@login_required
def address_detail(request, pk):
    """View address details with map"""
    address = get_object_or_404(Address, pk=pk, is_deleted=False, hr_person__isnull=False)
    context = {
        'address': address,
    }
    return render(request, 'hr/address_detail.html', context)


@login_required
def address_edit(request, pk):
    """Edit address with map integration"""
    address = get_object_or_404(Address, pk=pk, is_deleted=False, hr_person__isnull=False)

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            address.updated_by = request.user
            address.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('hr:address_detail', pk=address.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm(instance=address)

    context = {
        'form': form,
        'address': address,
    }
    return render(request, 'hr/address_form.html', context)


@login_required
def address_delete(request, pk):
    """Soft delete address"""
    address = get_object_or_404(Address, pk=pk, is_deleted=False, hr_person__isnull=False)

    if request.method == 'POST':
        # Soft delete
        address.is_deleted = True
        address.deleted_at = datetime.now()
        address.updated_by = request.user
        address.save()
        messages.success(request, f'Address deleted successfully.')
        return redirect('hr:address_list')

    # If GET request, redirect to list
    return redirect('hr:address_list')


# ========== Reports and Settings ==========
@login_required
def reports(request):
    """HR Reports dashboard"""
    return render(request, 'hr/reports.html')


@login_required
def settings(request):
    """HR Settings"""
    return render(request, 'hr/settings.html')

# -------------------------------------------------
# Position list views (used by dashboard + wizard)
# -------------------------------------------------
@login_required
def position_list(request):
    """
    Simple HTML list of positions, linked from hr_dashboard.html.
    """
    positions = (
        Position.objects
        .select_related("department")
        .filter(is_active=True)
        .order_by("department__name", "name")
    )
    return render(request, "hr/position_list.html", {"positions": positions})


@login_required
def position_list_api(request):
    """
    JSON API used by employee_wizard_employee.html to populate the
    Position dropdown based on ?department=<id>.
    """
    department_id = request.GET.get("department")

    qs = Position.objects.filter(is_active=True)
    if department_id:
        qs = qs.filter(department_id=department_id)

    data = [
        {
            "id": p.id,
            "name": p.name,
            "department": p.department.name,
            "level": p.position_level,
            "salary_grade": p.salary_grade,
        }
        for p in qs
    ]
    return JsonResponse({"results": data})


@login_required
def department_list_api(request):
    """
    JSON API to get list of all departments for dropdowns.
    Used by employee_wizard_employee.html to populate department select.
    """
    qs = Department.objects.all().order_by('name')

    data = [
        {
            "id": dept.id,
            "name": dept.name,
            "type": dept.department_type,
            "description": dept.description or "",
        }
        for dept in qs
    ]
    return JsonResponse({"results": data})


@login_required
def employee_list_api(request):
    """
    JSON API to get list of employees for supervisor selection.
    Used by employee_wizard_employee.html to populate report_to dropdown.
    Filters by status if provided.
    """
    status = request.GET.get("status", "")
    department_id = request.GET.get("department", "")

    qs = HREmployee.objects.filter(is_deleted=False).select_related('person', 'position', 'department')

    if status:
        qs = qs.filter(status=status)

    if department_id:
        qs = qs.filter(department_id=department_id)

    # Order by department then by name
    qs = qs.order_by('department__name', 'person__first_name_en', 'person__last_name_en')

    data = [
        {
            "id": emp.id,
            "employee_no": emp.employee_no,
            "full_name": emp.person.get_full_name_en() if hasattr(emp.person, 'get_full_name_en') else f"{emp.person.first_name_en} {emp.person.last_name_en}",
            "position": emp.position.name if emp.position else "",
            "department": emp.department.name if emp.department else "",
            "status": emp.status,
        }
        for emp in qs
    ]
    return JsonResponse({"results": data})
