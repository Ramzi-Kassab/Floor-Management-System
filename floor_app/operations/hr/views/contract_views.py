"""
HR Contract Management Views

Views for managing employee contracts, compensation, and employment terms.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import csv

from ..models import HRContract, HREmployee
from ..decorators import hr_manager_required


# ============================================================================
# CONTRACT LIST & DASHBOARD
# ============================================================================

class ContractListView(ListView):
    """List all employee contracts."""
    model = HRContract
    template_name = 'hr/contracts/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 25

    def get_queryset(self):
        queryset = HRContract.objects.select_related(
            'employee__person',
            'currency',
            'created_by'
        ).order_by('-is_current', '-start_date')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(contract_number__icontains=search) |
                Q(employee__employee_code__icontains=search) |
                Q(employee__person__first_name__icontains=search) |
                Q(employee__person__last_name__icontains=search)
            )

        # Contract type filter
        contract_type = self.request.GET.get('contract_type')
        if contract_type:
            queryset = queryset.filter(contract_type=contract_type)

        # Status filter
        status = self.request.GET.get('status')
        if status == 'current':
            queryset = queryset.filter(is_current=True)
        elif status == 'expired':
            queryset = queryset.filter(
                is_current=False,
                end_date__lt=timezone.now().date()
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract_types'] = HRContract.CONTRACT_TYPE_CHOICES
        context['selected_type'] = self.request.GET.get('contract_type', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')

        # Statistics
        context['stats'] = {
            'total_contracts': HRContract.objects.count(),
            'current_contracts': HRContract.objects.filter(is_current=True).count(),
            'permanent_contracts': HRContract.objects.filter(contract_type='permanent').count(),
            'temporary_contracts': HRContract.objects.filter(contract_type='temporary').count(),
        }

        return context


@login_required
@hr_manager_required
def contract_dashboard(request):
    """Contract management dashboard with statistics and insights."""
    today = timezone.now().date()

    # Get contract statistics
    stats = {
        'total_contracts': HRContract.objects.count(),
        'active_contracts': HRContract.objects.filter(is_current=True).count(),
        'expiring_soon': HRContract.objects.filter(
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=today + timezone.timedelta(days=90)
        ).count(),
        'expired_contracts': HRContract.objects.filter(
            end_date__lt=today
        ).count(),
    }

    # Contracts by type
    contracts_by_type = {}
    for code, name in HRContract.CONTRACT_TYPE_CHOICES:
        count = HRContract.objects.filter(contract_type=code, is_current=True).count()
        contracts_by_type[name] = count

    # Recent contracts
    recent_contracts = HRContract.objects.select_related(
        'employee__person',
        'currency'
    ).order_by('-created_at')[:10]

    # Expiring contracts
    expiring_contracts = HRContract.objects.filter(
        end_date__isnull=False,
        end_date__gte=today,
        end_date__lte=today + timezone.timedelta(days=90)
    ).select_related('employee__person').order_by('end_date')[:10]

    context = {
        'stats': stats,
        'contracts_by_type': contracts_by_type,
        'recent_contracts': recent_contracts,
        'expiring_contracts': expiring_contracts,
    }

    return render(request, 'hr/contracts/dashboard.html', context)


# ============================================================================
# CONTRACT DETAIL
# ============================================================================

class ContractDetailView(DetailView):
    """View contract details."""
    model = HRContract
    template_name = 'hr/contracts/contract_detail.html'
    context_object_name = 'contract'

    def get_queryset(self):
        return HRContract.objects.select_related(
            'employee__person',
            'employee__department',
            'employee__position',
            'currency',
            'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = self.object

        # Get other contracts for this employee
        context['other_contracts'] = HRContract.objects.filter(
            employee=contract.employee
        ).exclude(pk=contract.pk).order_by('-start_date')

        # Check if contract is ending soon
        if contract.end_date:
            days_until_end = (contract.end_date - timezone.now().date()).days
            context['days_until_end'] = days_until_end
            context['ending_soon'] = 0 < days_until_end <= 90

        return context


# ============================================================================
# CONTRACT CREATE/UPDATE
# ============================================================================

class ContractCreateView(CreateView):
    """Create a new employee contract."""
    model = HRContract
    template_name = 'hr/contracts/contract_form.html'
    fields = [
        'employee', 'contract_type', 'start_date', 'end_date',
        'basic_salary', 'housing_allowance', 'transport_allowance',
        'other_allowances', 'currency', 'is_current',
        'probation_period_months', 'notice_period_days',
        'work_hours_per_week', 'annual_leave_days',
        'contract_file', 'notes'
    ]

    def get_initial(self):
        initial = super().get_initial()

        # Pre-fill employee if provided in URL
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                employee = HREmployee.objects.get(pk=employee_id)
                initial['employee'] = employee
                initial['is_current'] = True
            except HREmployee.DoesNotExist:
                pass

        # Default currency to SAR
        initial['currency'] = 'SAR'
        initial['work_hours_per_week'] = 40
        initial['annual_leave_days'] = 21

        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Contract created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:contract_detail', kwargs={'pk': self.object.pk})


class ContractUpdateView(UpdateView):
    """Update an existing contract."""
    model = HRContract
    template_name = 'hr/contracts/contract_form.html'
    fields = [
        'employee', 'contract_type', 'start_date', 'end_date',
        'basic_salary', 'housing_allowance', 'transport_allowance',
        'other_allowances', 'currency', 'is_current',
        'probation_period_months', 'notice_period_days',
        'work_hours_per_week', 'annual_leave_days',
        'contract_file', 'notes'
    ]

    def form_valid(self, form):
        messages.success(self.request, 'Contract updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:contract_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# CONTRACT ACTIONS
# ============================================================================

@login_required
@hr_manager_required
def contract_renew(request, pk):
    """Renew a contract (create a new contract based on existing one)."""
    old_contract = get_object_or_404(HRContract, pk=pk)

    if request.method == 'POST':
        # Create new contract based on old one
        new_contract = HRContract()
        new_contract.employee = old_contract.employee
        new_contract.contract_type = old_contract.contract_type
        new_contract.basic_salary = old_contract.basic_salary
        new_contract.housing_allowance = old_contract.housing_allowance
        new_contract.transport_allowance = old_contract.transport_allowance
        new_contract.other_allowances = old_contract.other_allowances
        new_contract.currency = old_contract.currency
        new_contract.work_hours_per_week = old_contract.work_hours_per_week
        new_contract.annual_leave_days = old_contract.annual_leave_days
        new_contract.created_by = request.user

        # Get new contract details from form
        new_contract.start_date = request.POST.get('start_date')
        new_contract.end_date = request.POST.get('end_date') or None
        new_contract.is_current = True
        new_contract.notes = request.POST.get('notes', '')

        # Mark old contract as not current
        old_contract.is_current = False
        old_contract.save()

        new_contract.save()

        messages.success(request, f'Contract renewed successfully. New contract: {new_contract.contract_number}')
        return redirect('hr:contract_detail', pk=new_contract.pk)

    context = {
        'old_contract': old_contract,
        'suggested_start_date': old_contract.end_date if old_contract.end_date else timezone.now().date(),
    }

    return render(request, 'hr/contracts/contract_renew.html', context)


@login_required
@hr_manager_required
def contract_terminate(request, pk):
    """Terminate a contract."""
    contract = get_object_or_404(HRContract, pk=pk)

    if request.method == 'POST':
        termination_date = request.POST.get('termination_date')
        termination_reason = request.POST.get('termination_reason', '')

        # Update contract
        contract.end_date = termination_date
        contract.is_current = False
        contract.notes = f"{contract.notes}\n\nTerminated on {termination_date}. Reason: {termination_reason}"
        contract.save()

        # Update employee status
        contract.employee.termination_date = termination_date
        contract.employee.employment_status = 'terminated'
        contract.employee.is_active = False
        contract.employee.save()

        messages.success(request, 'Contract terminated successfully.')
        return redirect('hr:contract_detail', pk=contract.pk)

    context = {
        'contract': contract,
    }

    return render(request, 'hr/contracts/contract_terminate.html', context)


# ============================================================================
# REPORTS & EXPORTS
# ============================================================================

@login_required
@hr_manager_required
def contract_report(request):
    """Generate contract reports."""
    # Get filters
    report_type = request.GET.get('type', 'summary')

    contracts = HRContract.objects.select_related(
        'employee__person',
        'employee__department',
        'currency'
    )

    # Apply filters
    contract_type = request.GET.get('contract_type')
    if contract_type:
        contracts = contracts.filter(contract_type=contract_type)

    department = request.GET.get('department')
    if department:
        contracts = contracts.filter(employee__department_id=department)

    context = {
        'contracts': contracts,
        'report_type': report_type,
    }

    return render(request, 'hr/contracts/contract_report.html', context)


@login_required
@hr_manager_required
def export_contracts_csv(request):
    """Export contracts to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contracts.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Contract Number', 'Employee Code', 'Employee Name',
        'Contract Type', 'Start Date', 'End Date',
        'Basic Salary', 'Housing Allowance', 'Transport Allowance',
        'Other Allowances', 'Total Compensation', 'Currency',
        'Status'
    ])

    contracts = HRContract.objects.select_related(
        'employee__person',
        'currency'
    ).order_by('-start_date')

    for contract in contracts:
        writer.writerow([
            contract.contract_number,
            contract.employee.employee_code,
            contract.employee.person.full_name,
            contract.get_contract_type_display(),
            contract.start_date,
            contract.end_date or '',
            contract.basic_salary,
            contract.housing_allowance,
            contract.transport_allowance,
            contract.other_allowances,
            contract.total_compensation,
            contract.currency.code if contract.currency else '',
            'Current' if contract.is_current else 'Not Current'
        ])

    return response
