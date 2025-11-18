"""
Leave Management Views
Comprehensive views for leave policies, balances, requests, and approvals
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.http import JsonResponse, FileResponse, Http404
from datetime import datetime, timedelta
import calendar

from floor_app.operations.hr.models import (
    LeavePolicy, LeaveBalance, LeaveRequest,
    LeaveType, LeaveRequestStatus, HREmployee
)
from floor_app.operations.hr.forms.leave_forms import (
    LeavePolicyForm, LeaveBalanceForm, LeaveRequestForm,
    LeaveRequestApprovalForm, LeaveRequestSearchForm
)


def staff_or_manager_required(user):
    """Check if user is staff or manager"""
    return user.is_staff or hasattr(user, 'hremployee') and user.hremployee.department and user.hremployee.department.manager == user.hremployee


# ============================================================================
# LEAVE POLICY VIEWS
# ============================================================================

class LeavePolicyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all leave policies"""
    model = LeavePolicy
    template_name = 'hr/leave/policy_list.html'
    context_object_name = 'policies'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = LeavePolicy.objects.filter(is_deleted=False)

        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=(is_active == 'true'))

        # Filter by leave type
        leave_type = self.request.GET.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)

        return queryset.order_by('leave_type', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['leave_types'] = LeaveType.CHOICES
        return context


class LeavePolicyDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View leave policy details"""
    model = LeavePolicy
    template_name = 'hr/leave/policy_detail.html'
    context_object_name = 'policy'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return LeavePolicy.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get statistics for this policy
        current_year = timezone.now().year
        context['balances_count'] = self.object.balances.filter(year=current_year).count()
        context['requests_count'] = self.object.requests.filter(start_date__year=current_year).count()
        context['pending_requests'] = self.object.requests.filter(
            status=LeaveRequestStatus.PENDING_APPROVAL
        ).count()
        return context


class LeavePolicyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new leave policy"""
    model = LeavePolicy
    form_class = LeavePolicyForm
    template_name = 'hr/leave/policy_form.html'
    success_url = reverse_lazy('hr:leave_policy_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, f'Leave policy "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class LeavePolicyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update leave policy"""
    model = LeavePolicy
    form_class = LeavePolicyForm
    template_name = 'hr/leave/policy_form.html'
    success_url = reverse_lazy('hr:leave_policy_list')

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return LeavePolicy.objects.filter(is_deleted=False)

    def form_valid(self, form):
        messages.success(self.request, f'Leave policy "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


# ============================================================================
# LEAVE BALANCE VIEWS
# ============================================================================

@login_required
@user_passes_test(staff_or_manager_required)
def leave_balance_dashboard(request):
    """Dashboard showing all leave balances"""
    current_year = timezone.now().year
    year = int(request.GET.get('year', current_year))

    # Get all employees with balances
    balances = LeaveBalance.objects.filter(
        year=year,
        employee__is_deleted=False
    ).select_related(
        'employee', 'leave_policy'
    ).order_by('employee__employee_no', 'leave_policy__leave_type')

    # Filter by employee if specified
    employee_id = request.GET.get('employee')
    if employee_id:
        balances = balances.filter(employee_id=employee_id)

    # Filter by department if specified
    department_id = request.GET.get('department')
    if department_id:
        balances = balances.filter(employee__department_id=department_id)

    # Calculate summary statistics
    total_accrued = balances.aggregate(Sum('accrued'))['accrued__sum'] or 0
    total_used = balances.aggregate(Sum('used'))['used__sum'] or 0
    total_pending = balances.aggregate(Sum('pending'))['pending__sum'] or 0

    # Get list of employees and departments for filters
    employees = HREmployee.objects.filter(is_deleted=False).order_by('employee_no')
    from floor_app.operations.hr.models import Department
    departments = Department.objects.all().order_by('name')

    context = {
        'balances': balances,
        'year': year,
        'years': range(current_year - 2, current_year + 2),
        'total_accrued': total_accrued,
        'total_used': total_used,
        'total_pending': total_pending,
        'employees': employees,
        'departments': departments,
    }

    return render(request, 'hr/leave/balance_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def leave_balance_adjust(request, pk):
    """Adjust leave balance"""
    balance = get_object_or_404(LeaveBalance, pk=pk)

    if request.method == 'POST':
        form = LeaveBalanceForm(request.POST, instance=balance)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Balance adjusted for {balance.employee.employee_no} - {balance.leave_policy.name}'
            )
            return redirect('hr:leave_balance_dashboard')
    else:
        form = LeaveBalanceForm(instance=balance)

    return render(request, 'hr/leave/balance_adjust.html', {
        'form': form,
        'balance': balance,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def leave_balance_initialize(request):
    """Initialize leave balances for employees"""
    if request.method == 'POST':
        year = int(request.POST.get('year', timezone.now().year))
        employee_ids = request.POST.getlist('employees')
        policy_ids = request.POST.getlist('policies')

        created_count = 0
        for employee_id in employee_ids:
            for policy_id in policy_ids:
                try:
                    employee = HREmployee.objects.get(pk=employee_id, is_deleted=False)
                    policy = LeavePolicy.objects.get(pk=policy_id, is_deleted=False)

                    # Check if balance already exists
                    balance, created = LeaveBalance.objects.get_or_create(
                        employee=employee,
                        leave_policy=policy,
                        year=year,
                        defaults={
                            'opening_balance': policy.annual_entitlement_days,
                            'accrued': policy.annual_entitlement_days if policy.accrual_type == 'UPFRONT' else 0,
                        }
                    )
                    if created:
                        created_count += 1
                except Exception as e:
                    messages.error(request, f'Error initializing balance: {e}')

        messages.success(request, f'Initialized {created_count} leave balance(s) successfully!')
        return redirect('hr:leave_balance_dashboard')

    # GET request - show form
    current_year = timezone.now().year
    employees = HREmployee.objects.filter(is_deleted=False).order_by('employee_no')
    policies = LeavePolicy.objects.filter(is_deleted=False, is_active=True).order_by('leave_type')

    return render(request, 'hr/leave/balance_initialize.html', {
        'employees': employees,
        'policies': policies,
        'years': range(current_year, current_year + 2),
    })


# ============================================================================
# LEAVE REQUEST VIEWS
# ============================================================================

class LeaveRequestListView(LoginRequiredMixin, ListView):
    """List leave requests"""
    model = LeaveRequest
    template_name = 'hr/leave/request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        queryset = LeaveRequest.objects.filter(
            is_deleted=False
        ).select_related(
            'employee', 'leave_policy'
        ).order_by('-created_at')

        # If not staff, only show own requests
        if not self.request.user.is_staff:
            try:
                employee = self.request.user.hremployee
                queryset = queryset.filter(employee=employee)
            except:
                queryset = queryset.none()

        # Apply filters from search form
        form = LeaveRequestSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('employee'):
                queryset = queryset.filter(employee=form.cleaned_data['employee'])
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('leave_type'):
                queryset = queryset.filter(leave_policy__leave_type=form.cleaned_data['leave_type'])
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(start_date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(end_date__lte=form.cleaned_data['date_to'])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = LeaveRequestSearchForm(self.request.GET)

        # Add summary statistics
        queryset = self.get_queryset()
        context['total_requests'] = queryset.count()
        context['pending_count'] = queryset.filter(status=LeaveRequestStatus.PENDING_APPROVAL).count()
        context['approved_count'] = queryset.filter(status=LeaveRequestStatus.APPROVED).count()

        return context


class LeaveRequestDetailView(LoginRequiredMixin, DetailView):
    """View leave request details"""
    model = LeaveRequest
    template_name = 'hr/leave/request_detail.html'
    context_object_name = 'request'

    def get_queryset(self):
        queryset = LeaveRequest.objects.filter(is_deleted=False)

        # If not staff, only show own requests
        if not self.request.user.is_staff:
            try:
                employee = self.request.user.hremployee
                queryset = queryset.filter(employee=employee)
            except:
                queryset = queryset.none()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get employee's current balance
        try:
            balance = LeaveBalance.objects.get(
                employee=self.object.employee,
                leave_policy=self.object.leave_policy,
                year=self.object.start_date.year
            )
            context['balance'] = balance
        except LeaveBalance.DoesNotExist:
            context['balance'] = None

        # Check if user can approve
        context['can_approve'] = (
            self.request.user.is_staff or
            (hasattr(self.request.user, 'hremployee') and
             self.request.user.hremployee.department and
             self.request.user.hremployee.department.manager == self.request.user.hremployee)
        )

        return context


class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    """Create new leave request"""
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'hr/leave/request_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('hr:leave_request_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # Handle file upload for medical certificate
        if 'attachment' in self.request.FILES:
            # Save file (you'll need to configure media storage)
            attachment = self.request.FILES['attachment']
            # For now, just store the filename
            form.instance.attachment_path = f'leave_attachments/{attachment.name}'

        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Leave request {form.instance.request_number} created successfully!'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's leave balances
        try:
            employee = self.request.user.hremployee
            current_year = timezone.now().year
            context['balances'] = LeaveBalance.objects.filter(
                employee=employee,
                year=current_year
            ).select_related('leave_policy')
        except:
            context['balances'] = []

        return context


@login_required
def leave_request_submit(request, pk):
    """Submit leave request for approval"""
    leave_request = get_object_or_404(LeaveRequest, pk=pk, is_deleted=False)

    # Check ownership
    if not request.user.is_staff:
        try:
            if leave_request.employee != request.user.hremployee:
                messages.error(request, 'You can only submit your own leave requests.')
                return redirect('hr:leave_request_list')
        except:
            messages.error(request, 'Employee record not found.')
            return redirect('hr:leave_request_list')

    if leave_request.submit():
        messages.success(request, f'Leave request {leave_request.request_number} submitted for approval!')
    else:
        messages.error(request, 'Leave request cannot be submitted in current status.')

    return redirect('hr:leave_request_detail', pk=pk)


@login_required
@user_passes_test(staff_or_manager_required)
def leave_request_approve(request, pk):
    """Approve or reject leave request"""
    leave_request = get_object_or_404(
        LeaveRequest,
        pk=pk,
        is_deleted=False,
        status=LeaveRequestStatus.PENDING_APPROVAL
    )

    if request.method == 'POST':
        form = LeaveRequestApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data['notes']

            try:
                employee_id = request.user.hremployee.id
            except:
                employee_id = request.user.id

            if action == 'approve':
                if leave_request.approve(employee_id, notes):
                    messages.success(
                        request,
                        f'Leave request {leave_request.request_number} approved!'
                    )
                else:
                    messages.error(request, 'Failed to approve leave request.')
            else:  # reject
                if leave_request.reject(employee_id, notes):
                    messages.warning(
                        request,
                        f'Leave request {leave_request.request_number} rejected.'
                    )
                else:
                    messages.error(request, 'Failed to reject leave request.')

            return redirect('hr:leave_request_detail', pk=pk)
    else:
        form = LeaveRequestApprovalForm()

    return render(request, 'hr/leave/request_approve.html', {
        'leave_request': leave_request,
        'form': form,
    })


@login_required
def leave_request_cancel(request, pk):
    """Cancel leave request"""
    leave_request = get_object_or_404(LeaveRequest, pk=pk, is_deleted=False)

    # Check ownership
    if not request.user.is_staff:
        try:
            if leave_request.employee != request.user.hremployee:
                messages.error(request, 'You can only cancel your own leave requests.')
                return redirect('hr:leave_request_list')
        except:
            messages.error(request, 'Employee record not found.')
            return redirect('hr:leave_request_list')

    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason', '')

        leave_request.status = LeaveRequestStatus.CANCELLED
        leave_request.cancelled_at = timezone.now()
        leave_request.cancellation_reason = reason
        leave_request.save()

        # Release pending balance
        try:
            balance = LeaveBalance.objects.get(
                employee=leave_request.employee,
                leave_policy=leave_request.leave_policy,
                year=leave_request.start_date.year
            )
            balance.release_pending(leave_request.total_days)
        except LeaveBalance.DoesNotExist:
            pass

        messages.success(request, f'Leave request {leave_request.request_number} cancelled.')
        return redirect('hr:leave_request_detail', pk=pk)

    return render(request, 'hr/leave/request_cancel.html', {
        'leave_request': leave_request,
    })


@login_required
def leave_calendar(request):
    """Calendar view of all approved leaves"""
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    # Get approved leave requests for the month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    leave_requests = LeaveRequest.objects.filter(
        is_deleted=False,
        status=LeaveRequestStatus.APPROVED,
        start_date__lt=end_date,
        end_date__gte=start_date
    ).select_related('employee', 'leave_policy')

    # Build calendar
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    # Organize leaves by date
    leaves_by_date = {}
    for leave_req in leave_requests:
        current_date = leave_req.start_date
        while current_date <= leave_req.end_date:
            if start_date <= current_date < end_date:
                date_key = current_date.day
                if date_key not in leaves_by_date:
                    leaves_by_date[date_key] = []
                leaves_by_date[date_key].append(leave_req)
            current_date += timedelta(days=1)

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'calendar': cal,
        'leaves_by_date': leaves_by_date,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
    }

    return render(request, 'hr/leave/calendar.html', context)


@login_required
def my_leave_dashboard(request):
    """Employee's personal leave dashboard"""
    try:
        employee = request.user.hremployee
    except:
        messages.error(request, 'Employee record not found.')
        return redirect('hr:dashboard')

    current_year = timezone.now().year

    # Get leave balances
    balances = LeaveBalance.objects.filter(
        employee=employee,
        year=current_year
    ).select_related('leave_policy')

    # Get recent leave requests
    recent_requests = LeaveRequest.objects.filter(
        employee=employee,
        is_deleted=False
    ).select_related('leave_policy').order_by('-created_at')[:10]

    # Get pending requests
    pending_requests = recent_requests.filter(status=LeaveRequestStatus.PENDING_APPROVAL)

    # Get upcoming approved leaves
    upcoming_leaves = LeaveRequest.objects.filter(
        employee=employee,
        is_deleted=False,
        status=LeaveRequestStatus.APPROVED,
        start_date__gte=timezone.now().date()
    ).order_by('start_date')[:5]

    context = {
        'employee': employee,
        'balances': balances,
        'recent_requests': recent_requests,
        'pending_requests': pending_requests,
        'upcoming_leaves': upcoming_leaves,
        'current_year': current_year,
    }

    return render(request, 'hr/leave/my_dashboard.html', context)
