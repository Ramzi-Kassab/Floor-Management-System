"""
HR Employee Portal Views

Employee self-service portal views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from .models import EmployeeRequest


@login_required
def portal_dashboard(request):
    """Employee portal dashboard - my overview."""
    try:
        employee = request.user.hr_employee
    except:
        messages.error(request, 'No employee record found for your account.')
        return redirect('skeleton:dashboard')

    # Get leave balance
    current_year = timezone.now().year
    leave_balances = employee.leave_balances.filter(year=current_year)

    # Get pending requests
    pending_requests = employee.portal_requests.filter(
        status__in=['submitted', 'under_review']
    ).count()

    # Get recent leave requests
    recent_leaves = employee.leave_requests.all()[:5]

    # Get upcoming training
    upcoming_training = employee.training_enrollments.filter(
        status='enrolled'
    ).select_related('session__program')[:5]

    # Get pending documents for renewal
    pending_docs = employee.documents.filter(
        status='active',
        expiry_date__lte=timezone.now().date() + timezone.timedelta(days=90)
    )[:5]

    context = {
        'employee': employee,
        'leave_balances': leave_balances,
        'pending_requests': pending_requests,
        'recent_leaves': recent_leaves,
        'upcoming_training': upcoming_training,
        'pending_docs': pending_docs,
    }

    return render(request, 'hr_portal/dashboard.html', context)


@login_required
def my_leave(request):
    """My leave requests and balance."""
    try:
        employee = request.user.hr_employee
    except:
        messages.error(request, 'No employee record found for your account.')
        return redirect('skeleton:dashboard')

    current_year = timezone.now().year
    leave_balances = employee.leave_balances.filter(year=current_year)
    leave_requests = employee.leave_requests.all().order_by('-start_date')

    context = {
        'employee': employee,
        'leave_balances': leave_balances,
        'leave_requests': leave_requests,
    }

    return render(request, 'hr_portal/my_leave.html', context)


@login_required
def my_requests(request):
    """My requests to HR."""
    try:
        employee = request.user.hr_employee
    except:
        messages.error(request, 'No employee record found for your account.')
        return redirect('skeleton:dashboard')

    requests = employee.portal_requests.all()

    context = {
        'employee': employee,
        'requests': requests,
    }

    return render(request, 'hr_portal/my_requests.html', context)


@login_required
def submit_request(request):
    """Submit a new request."""
    try:
        employee = request.user.hr_employee
    except:
        messages.error(request, 'No employee record found for your account.')
        return redirect('skeleton:dashboard')

    if request.method == 'POST':
        emp_request = EmployeeRequest()
        emp_request.employee = employee
        emp_request.request_type = request.POST.get('request_type')
        emp_request.subject = request.POST.get('subject')
        emp_request.description = request.POST.get('description')
        emp_request.priority = request.POST.get('priority', 'normal')

        if request.FILES.get('attachment'):
            emp_request.attachment = request.FILES['attachment']

        emp_request.save()

        messages.success(request, f'Request {emp_request.request_number} submitted successfully.')
        return redirect('hr_portal:my_requests')

    context = {
        'employee': employee,
        'request_types': EmployeeRequest.REQUEST_TYPE_CHOICES,
        'priorities': EmployeeRequest.PRIORITY_CHOICES,
    }

    return render(request, 'hr_portal/submit_request.html', context)


@login_required
def my_documents(request):
    """My documents."""
    try:
        employee = request.user.hr_employee
    except:
        messages.error(request, 'No employee record found for your account.')
        return redirect('skeleton:dashboard')

    documents = employee.documents.all().order_by('-issue_date')

    context = {
        'employee': employee,
        'documents': documents,
    }

    return render(request, 'hr_portal/my_documents.html', context)


@login_required
def my_training(request):
    """My training history and enrollments."""
    try:
        employee = request.user.hr_employee
    except:
        messages.error(request, 'No employee record found for your account.')
        return redirect('skeleton:dashboard')

    training_enrollments = employee.training_enrollments.all().select_related(
        'session__program'
    ).order_by('-enrollment_date')

    context = {
        'employee': employee,
        'training_enrollments': training_enrollments,
    }

    return render(request, 'hr_portal/my_training.html', context)
