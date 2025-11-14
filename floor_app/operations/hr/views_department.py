from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Department


class DepartmentListView(LoginRequiredMixin, ListView):
    """Display all departments in a grid layout."""
    model = Department
    template_name = 'hr/department_list.html'
    context_object_name = 'departments'
    paginate_by = 12
    login_url = reverse_lazy('login')

    def get_queryset(self):
        """Filter departments by search and type."""
        queryset = Department.objects.all()

        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(name__icontains=search)

        dept_type = self.request.GET.get('type', '').strip()
        if dept_type:
            queryset = queryset.filter(department_type=dept_type)

        sort_by = self.request.GET.get('sort', 'name')
        if sort_by in ['name', '-name', 'department_type', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['dept_type'] = self.request.GET.get('type', '')
        context['sort_by'] = self.request.GET.get('sort', 'name')
        context['department_types'] = Department.DEPARTMENT_TYPE_CHOICES
        context['total_count'] = self.get_queryset().count()
        return context


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    """Display detailed information about a single department."""
    model = Department
    template_name = 'hr/department_detail.html'
    context_object_name = 'department'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # You can add related employees count here when ready
        return context


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Create a new department."""
    model = Department
    template_name = 'hr/department_form.html'
    fields = ['name', 'description', 'department_type']
    success_url = reverse_lazy('hr:department_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        """Save form and show success message."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Department "{self.object.name}" has been created successfully.'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = True
        context['department_types'] = Department.DEPARTMENT_TYPE_CHOICES
        return context


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing department."""
    model = Department
    template_name = 'hr/department_form.html'
    fields = ['name', 'description', 'department_type']
    success_url = reverse_lazy('hr:department_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        """Save form and show success message."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Department "{self.object.name}" has been updated successfully.'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = False
        context['department_types'] = Department.DEPARTMENT_TYPE_CHOICES
        return context


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a department with confirmation."""
    model = Department
    template_name = 'hr/department_confirm_delete.html'
    success_url = reverse_lazy('hr:department_list')
    login_url = reverse_lazy('login')

    def delete(self, request, *args, **kwargs):
        """Delete and show success message."""
        department_name = self.get_object().name
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'Department "{department_name}" has been deleted successfully.'
        )
        return response


# Function-based views for quick actions (optional)
@login_required
def department_list(request):
    """Function-based alternative to DepartmentListView."""
    departments = Department.objects.all()

    search = request.GET.get('search', '').strip()
    if search:
        departments = departments.filter(name__icontains=search)

    dept_type = request.GET.get('type', '').strip()
    if dept_type:
        departments = departments.filter(department_type=dept_type)

    sort_by = request.GET.get('sort', 'name')
    if sort_by in ['name', '-name', 'department_type', 'created_at', '-created_at']:
        departments = departments.order_by(sort_by)

    context = {
        'departments': departments,
        'search': search,
        'dept_type': dept_type,
        'sort_by': sort_by,
        'department_types': Department.DEPARTMENT_TYPE_CHOICES,
        'total_count': departments.count(),
    }
    return render(request, 'hr/department_list.html', context)
