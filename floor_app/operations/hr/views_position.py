from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from .models import Position, Department


class PositionListView(LoginRequiredMixin, ListView):
    """Display all positions with filtering and search."""
    model = Position
    template_name = 'hr/position_list.html'
    context_object_name = 'positions'
    paginate_by = 20
    login_url = reverse_lazy('login')

    def get_queryset(self):
        """Filter positions by search, department, level, and status."""
        queryset = Position.objects.filter(is_deleted=False).select_related('department')

        # Search filter
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(department__name__icontains=search)
            )

        # Department filter
        department_id = self.request.GET.get('department', '').strip()
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        # Position level filter
        position_level = self.request.GET.get('level', '').strip()
        if position_level:
            queryset = queryset.filter(position_level=position_level)

        # Salary grade filter
        salary_grade = self.request.GET.get('grade', '').strip()
        if salary_grade:
            queryset = queryset.filter(salary_grade=salary_grade)

        # Active status filter
        is_active = self.request.GET.get('active', '').strip()
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        # Sort
        sort_by = self.request.GET.get('sort', 'department__name')
        if sort_by in ['name', '-name', 'department__name', '-department__name', 'position_level', '-position_level', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort_by, 'name')

        return queryset.annotate(num_employees=Count('employees', filter=Q(employees__is_deleted=False)))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['department_filter'] = self.request.GET.get('department', '')
        context['level_filter'] = self.request.GET.get('level', '')
        context['grade_filter'] = self.request.GET.get('grade', '')
        context['active_filter'] = self.request.GET.get('active', '')
        context['sort_by'] = self.request.GET.get('sort', 'department__name')

        # For filters
        context['departments'] = Department.objects.filter(is_deleted=False).order_by('name')
        context['position_levels'] = Position.POSITION_LEVEL_CHOICES
        context['salary_grades'] = Position.SALARY_GRADE_CHOICES

        # Statistics
        all_positions = Position.objects.filter(is_deleted=False)
        context['total_positions'] = all_positions.count()
        context['active_positions'] = all_positions.filter(is_active=True).count()

        return context


class PositionDetailView(LoginRequiredMixin, DetailView):
    """Display detailed information about a single position."""
    model = Position
    template_name = 'hr/position_detail.html'
    context_object_name = 'position'
    login_url = reverse_lazy('login')

    def get_queryset(self):
        return Position.objects.filter(is_deleted=False).select_related('department', 'auth_group')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get employees with this position (first 20)
        context['employees'] = self.object.employees.filter(
            is_deleted=False
        ).select_related('person')[:20]

        context['employee_count'] = self.object.employees.filter(is_deleted=False).count()

        return context


class PositionCreateView(LoginRequiredMixin, CreateView):
    """Create a new position."""
    model = Position
    template_name = 'hr/position_form.html'
    fields = [
        'name', 'description', 'department', 'position_level',
        'salary_grade', 'is_active', 'auth_group', 'permission_codenames'
    ]
    success_url = reverse_lazy('hr:position_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        """Save form with audit tracking and show success message."""
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Position "{self.object.name}" has been created successfully.'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Position'
        context['submit_text'] = 'Create Position'
        context['position_levels'] = Position.POSITION_LEVEL_CHOICES
        context['salary_grades'] = Position.SALARY_GRADE_CHOICES
        return context


class PositionUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing position."""
    model = Position
    template_name = 'hr/position_form.html'
    fields = [
        'name', 'description', 'department', 'position_level',
        'salary_grade', 'is_active', 'auth_group', 'permission_codenames'
    ]
    login_url = reverse_lazy('login')

    def get_queryset(self):
        return Position.objects.filter(is_deleted=False)

    def get_success_url(self):
        return reverse_lazy('hr:position_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        """Save form with audit tracking and show success message."""
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Position "{self.object.name}" has been updated successfully.'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Position: {self.object.name}'
        context['submit_text'] = 'Update Position'
        context['position_levels'] = Position.POSITION_LEVEL_CHOICES
        context['salary_grades'] = Position.SALARY_GRADE_CHOICES
        return context


class PositionDeleteView(LoginRequiredMixin, DeleteView):
    """Soft delete a position with confirmation."""
    model = Position
    template_name = 'hr/position_confirm_delete.html'
    success_url = reverse_lazy('hr:position_list')
    login_url = reverse_lazy('login')

    def get_queryset(self):
        return Position.objects.filter(is_deleted=False)

    def delete(self, request, *args, **kwargs):
        """Soft delete and show success message."""
        position = self.get_object()
        position_name = position.name

        # Check if position has active employees
        active_employee_count = position.employees.filter(is_deleted=False).count()
        if active_employee_count > 0:
            messages.error(
                request,
                f'Cannot delete position "{position_name}". It has {active_employee_count} active employee(s). '
                f'Please reassign or remove employees first.'
            )
            return redirect('hr:position_detail', pk=position.pk)

        # Perform soft delete
        position.is_deleted = True
        position.deleted_by = request.user
        position.save()

        messages.success(
            request,
            f'Position "{position_name}" has been deleted successfully.'
        )
        return redirect(self.success_url)


# Function-based views
@login_required
def position_list(request):
    """Function-based alternative to PositionListView."""
    positions = Position.objects.filter(is_deleted=False).select_related('department')

    # Search
    search = request.GET.get('search', '').strip()
    if search:
        positions = positions.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(department__name__icontains=search)
        )

    # Filters
    department_id = request.GET.get('department', '').strip()
    if department_id:
        positions = positions.filter(department_id=department_id)

    position_level = request.GET.get('level', '').strip()
    if position_level:
        positions = positions.filter(position_level=position_level)

    is_active = request.GET.get('active', '').strip()
    if is_active == 'true':
        positions = positions.filter(is_active=True)
    elif is_active == 'false':
        positions = positions.filter(is_active=False)

    # Sort
    sort_by = request.GET.get('sort', 'department__name')
    if sort_by in ['name', '-name', 'department__name', '-department__name', 'position_level', 'created_at']:
        positions = positions.order_by(sort_by, 'name')

    positions = positions.annotate(num_employees=Count('employees', filter=Q(employees__is_deleted=False)))

    context = {
        'positions': positions,
        'search': search,
        'department_filter': department_id,
        'level_filter': position_level,
        'active_filter': is_active,
        'sort_by': sort_by,
        'departments': Department.objects.filter(is_deleted=False).order_by('name'),
        'position_levels': Position.POSITION_LEVEL_CHOICES,
        'salary_grades': Position.SALARY_GRADE_CHOICES,
        'total_positions': Position.objects.filter(is_deleted=False).count(),
        'active_positions': Position.objects.filter(is_deleted=False, is_active=True).count(),
    }
    return render(request, 'hr/position_list.html', context)


@login_required
def position_list_api(request):
    """API endpoint for position list (JSON response)."""
    from django.http import JsonResponse

    positions = Position.objects.filter(is_deleted=False, is_active=True).select_related('department')

    search = request.GET.get('search', '').strip()
    if search:
        positions = positions.filter(
            Q(name__icontains=search) |
            Q(department__name__icontains=search)
        )

    data = [
        {
            'id': pos.id,
            'name': pos.name,
            'department': pos.department.name,
            'department_id': pos.department.id,
            'position_level': pos.get_position_level_display(),
            'salary_grade': pos.get_salary_grade_display(),
        }
        for pos in positions[:50]  # Limit to 50 results
    ]

    return JsonResponse({'positions': data})
