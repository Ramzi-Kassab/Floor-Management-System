"""
HR Shift Management Views

Views for managing shift templates and shift assignments.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.exceptions import ValidationError

from ..models import HRShiftTemplate, ShiftAssignment, HREmployee, Department
from ..decorators import hr_manager_required


# ============================================================================
# SHIFT TEMPLATE MANAGEMENT
# ============================================================================

class ShiftTemplateListView(ListView):
    """List all shift templates."""
    model = HRShiftTemplate
    template_name = 'hr/shifts/template_list.html'
    context_object_name = 'templates'
    paginate_by = 25

    def get_queryset(self):
        queryset = HRShiftTemplate.objects.select_related(
            'department',
            'cost_center'
        ).annotate(
            assignment_count=Count('assignments')
        ).order_by('code')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )

        # Active/Inactive filter
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Night shift filter
        is_night = self.request.GET.get('is_night')
        if is_night == '1':
            queryset = queryset.filter(is_night_shift=True)
        elif is_night == '0':
            queryset = queryset.filter(is_night_shift=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'total_templates': HRShiftTemplate.objects.count(),
            'active_templates': HRShiftTemplate.objects.filter(is_active=True).count(),
            'night_shifts': HRShiftTemplate.objects.filter(is_night_shift=True).count(),
            'total_assignments': ShiftAssignment.objects.filter(is_active=True).count(),
        }
        return context


class ShiftTemplateDetailView(DetailView):
    """View shift template details."""
    model = HRShiftTemplate
    template_name = 'hr/shifts/template_detail.html'
    context_object_name = 'template'

    def get_queryset(self):
        return HRShiftTemplate.objects.select_related(
            'department',
            'cost_center',
            'created_by'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = self.object

        # Get current assignments for this shift
        context['current_assignments'] = ShiftAssignment.objects.filter(
            shift_template=template,
            is_active=True,
            actual_return_date__isnull=True
        ).select_related('employee__person', 'employee__department')

        # Get assignment statistics
        context['total_assignments'] = ShiftAssignment.objects.filter(
            shift_template=template
        ).count()

        context['active_assignments'] = ShiftAssignment.objects.filter(
            shift_template=template,
            is_active=True
        ).count()

        return context


class ShiftTemplateCreateView(CreateView):
    """Create a new shift template."""
    model = HRShiftTemplate
    template_name = 'hr/shifts/template_form.html'
    fields = [
        'code', 'name', 'description',
        'start_time', 'end_time', 'duration_hours',
        'is_night_shift', 'working_days',
        'break_duration_minutes',
        'department', 'cost_center',
        'overtime_multiplier', 'is_active'
    ]

    def get_initial(self):
        initial = super().get_initial()
        initial['break_duration_minutes'] = 30
        initial['overtime_multiplier'] = 1.0
        initial['is_active'] = True
        initial['working_days'] = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Shift template created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:shift_template_detail', kwargs={'pk': self.object.pk})


class ShiftTemplateUpdateView(UpdateView):
    """Update an existing shift template."""
    model = HRShiftTemplate
    template_name = 'hr/shifts/template_form.html'
    fields = [
        'code', 'name', 'description',
        'start_time', 'end_time', 'duration_hours',
        'is_night_shift', 'working_days',
        'break_duration_minutes',
        'department', 'cost_center',
        'overtime_multiplier', 'is_active'
    ]

    def form_valid(self, form):
        messages.success(self.request, 'Shift template updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:shift_template_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# SHIFT ASSIGNMENT MANAGEMENT
# ============================================================================

class ShiftAssignmentListView(ListView):
    """List all shift assignments."""
    model = ShiftAssignment
    template_name = 'hr/shifts/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 25

    def get_queryset(self):
        queryset = ShiftAssignment.objects.select_related(
            'employee__person',
            'employee__department',
            'shift_template',
            'created_by'
        ).order_by('-start_date')

        # Search filter
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(employee__employee_code__icontains=search) |
                Q(employee__person__first_name__icontains=search) |
                Q(employee__person__last_name__icontains=search) |
                Q(shift_template__code__icontains=search) |
                Q(shift_template__name__icontains=search)
            )

        # Active/Inactive filter
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True, end_date__isnull=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'ended':
            queryset = queryset.filter(end_date__isnull=False)

        # Shift template filter
        shift_template = self.request.GET.get('shift_template')
        if shift_template:
            queryset = queryset.filter(shift_template_id=shift_template)

        # Department filter
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(employee__department_id=department)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shift_templates'] = HRShiftTemplate.objects.filter(is_active=True)
        context['departments'] = Department.objects.filter(is_active=True)
        context['stats'] = {
            'total_assignments': ShiftAssignment.objects.count(),
            'active_assignments': ShiftAssignment.objects.filter(is_active=True).count(),
            'employees_with_shifts': ShiftAssignment.objects.filter(
                is_active=True
            ).values('employee').distinct().count(),
        }
        return context


class ShiftAssignmentDetailView(DetailView):
    """View shift assignment details."""
    model = ShiftAssignment
    template_name = 'hr/shifts/assignment_detail.html'
    context_object_name = 'assignment'

    def get_queryset(self):
        return ShiftAssignment.objects.select_related(
            'employee__person',
            'employee__department',
            'employee__position',
            'shift_template',
            'created_by',
            'returned_by'
        )


class ShiftAssignmentCreateView(CreateView):
    """Create a new shift assignment."""
    model = ShiftAssignment
    template_name = 'hr/shifts/assignment_form.html'
    fields = [
        'employee', 'shift_template',
        'start_date', 'end_date',
        'is_active', 'notes'
    ]

    def get_initial(self):
        initial = super().get_initial()

        # Pre-fill employee if provided in URL
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                employee = HREmployee.objects.get(pk=employee_id)
                initial['employee'] = employee
            except HREmployee.DoesNotExist:
                pass

        # Pre-fill shift template if provided
        shift_id = self.request.GET.get('shift')
        if shift_id:
            try:
                shift = HRShiftTemplate.objects.get(pk=shift_id)
                initial['shift_template'] = shift
            except HRShiftTemplate.DoesNotExist:
                pass

        initial['start_date'] = timezone.now().date()
        initial['is_active'] = True

        return initial

    def form_valid(self, form):
        try:
            form.instance.created_by = self.request.user
            # Validate before saving
            form.instance.clean()
            messages.success(self.request, 'Shift assignment created successfully.')
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('hr:shift_assignment_detail', kwargs={'pk': self.object.pk})


class ShiftAssignmentUpdateView(UpdateView):
    """Update an existing shift assignment."""
    model = ShiftAssignment
    template_name = 'hr/shifts/assignment_form.html'
    fields = [
        'employee', 'shift_template',
        'start_date', 'end_date',
        'is_active', 'notes'
    ]

    def form_valid(self, form):
        try:
            # Validate before saving
            form.instance.clean()
            messages.success(self.request, 'Shift assignment updated successfully.')
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('hr:shift_assignment_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# SHIFT ACTIONS
# ============================================================================

@login_required
@hr_manager_required
def end_shift_assignment(request, pk):
    """End a shift assignment."""
    assignment = get_object_or_404(ShiftAssignment, pk=pk)

    if request.method == 'POST':
        end_date = request.POST.get('end_date')
        notes = request.POST.get('notes', '')

        assignment.end_date = end_date
        assignment.is_active = False
        if notes:
            assignment.notes = f"{assignment.notes}\n\n{notes}" if assignment.notes else notes
        assignment.save()

        messages.success(request, 'Shift assignment ended successfully.')
        return redirect('hr:shift_assignment_detail', pk=assignment.pk)

    context = {
        'assignment': assignment,
        'suggested_end_date': timezone.now().date(),
    }

    return render(request, 'hr/shifts/assignment_end.html', context)


# ============================================================================
# SHIFT SCHEDULE & CALENDAR
# ============================================================================

@login_required
@hr_manager_required
def shift_schedule(request):
    """View shift schedule/calendar."""
    # Get date range from request or default to current week
    from datetime import timedelta

    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday())  # Monday of current week
    end_date = start_date + timedelta(days=6)  # Sunday

    # Allow filtering by date range
    if request.GET.get('start_date'):
        start_date = request.GET.get('start_date')
    if request.GET.get('end_date'):
        end_date = request.GET.get('end_date')

    # Get all active shift assignments
    assignments = ShiftAssignment.objects.filter(
        is_active=True,
        start_date__lte=end_date
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=start_date)
    ).select_related(
        'employee__person',
        'employee__department',
        'shift_template'
    )

    # Allow filtering by department
    department = request.GET.get('department')
    if department:
        assignments = assignments.filter(employee__department_id=department)

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'assignments': assignments,
        'departments': Department.objects.filter(is_active=True),
    }

    return render(request, 'hr/shifts/schedule.html', context)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@login_required
def shift_template_api(request):
    """API endpoint for shift template data."""
    templates = HRShiftTemplate.objects.filter(is_active=True)

    # Filter by department if provided
    department = request.GET.get('department')
    if department:
        templates = templates.filter(department_id=department)

    data = []
    for template in templates:
        data.append({
            'id': template.pk,
            'code': template.code,
            'name': template.name,
            'start_time': template.start_time.strftime('%H:%M'),
            'end_time': template.end_time.strftime('%H:%M'),
            'duration_hours': str(template.duration_hours),
            'is_night_shift': template.is_night_shift,
            'working_days': template.working_days,
        })

    return JsonResponse({'templates': data})


@login_required
def employee_current_shift(request, employee_id):
    """Get employee's current shift assignment."""
    try:
        assignment = ShiftAssignment.objects.filter(
            employee_id=employee_id,
            is_active=True
        ).select_related('shift_template').latest('start_date')

        data = {
            'has_shift': True,
            'shift_code': assignment.shift_template.code,
            'shift_name': assignment.shift_template.name,
            'start_time': assignment.shift_template.start_time.strftime('%H:%M'),
            'end_time': assignment.shift_template.end_time.strftime('%H:%M'),
            'assignment_date': assignment.start_date.isoformat(),
        }
    except ShiftAssignment.DoesNotExist:
        data = {'has_shift': False}

    return JsonResponse(data)
