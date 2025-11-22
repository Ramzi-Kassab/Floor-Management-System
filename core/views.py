"""
Core app views.

Includes:
- Main dashboard
- User Preferences management
- API endpoints for table column preferences
- ERP reference management
- Loss of Sale tracking
- Django core tables front-end views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.urls import reverse_lazy
from floor_app.operations.hr.models import HREmployee, Department
import json

from .models import (
    UserPreference,
    CostCenter,
    ERPDocumentType,
    ERPReference,
    LossOfSaleCause,
    LossOfSaleEvent,
)
from .forms import (
    UserCreateForm,
    UserUpdateForm,
    UserPasswordChangeForm,
    GroupForm,
    UserPermissionsForm,
)
from .search_utils import GlobalSearch, SearchHistory


def home(request):
    """Public home page - landing page for unauthenticated users."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')


@login_required
def main_dashboard(request):
    """Main application dashboard."""
    # HR Summary
    hr_summary = {
        "employees": HREmployee.objects.filter(is_deleted=False).count(),
        "departments": Department.objects.count(),
    }

    # Inventory Summary
    try:
        from floor_app.operations.inventory.models import Item, SerialUnit
        inventory_summary = {
            "items": Item.objects.count(),
            "serial_units": SerialUnit.objects.count(),
        }
    except Exception:
        inventory_summary = {"items": 0, "serial_units": 0}

    # Production Summary
    try:
        from floor_app.operations.production.models import JobCard, ProductionBatch
        production_summary = {
            "job_cards": JobCard.objects.count(),
            "batches": ProductionBatch.objects.count(),
        }
    except Exception:
        production_summary = {"job_cards": 0, "batches": 0}

    # Evaluation Summary
    try:
        from floor_app.operations.evaluation.models import EvaluationSession, BitType
        evaluation_summary = {
            "sessions": EvaluationSession.objects.count(),
            "bit_types": BitType.objects.count(),
        }
    except Exception:
        evaluation_summary = {"sessions": 0, "bit_types": 0}

    # Purchasing Summary
    try:
        from floor_app.operations.purchasing.models import Supplier, PurchaseOrder
        purchasing_summary = {
            "suppliers": Supplier.objects.count(),
            "pos": PurchaseOrder.objects.count(),
        }
    except Exception:
        purchasing_summary = {"suppliers": 0, "pos": 0}

    # QRCodes Summary
    try:
        from floor_app.operations.qrcodes.models import QRCode, Equipment
        qrcodes_summary = {
            "codes": QRCode.objects.count(),
            "equipment": Equipment.objects.count(),
        }
    except Exception:
        qrcodes_summary = {"codes": 0, "equipment": 0}

    # Knowledge Summary
    try:
        from floor_app.operations.knowledge.models import Article, TrainingCourse
        knowledge_summary = {
            "articles": Article.objects.count(),
            "courses": TrainingCourse.objects.count(),
        }
    except Exception:
        knowledge_summary = {"articles": 0, "courses": 0}

    # Maintenance Summary
    try:
        from floor_app.operations.maintenance.models import Asset, WorkOrder
        maintenance_summary = {
            "assets": Asset.objects.count(),
            "work_orders": WorkOrder.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).count(),
        }
    except Exception:
        maintenance_summary = {"assets": 0, "work_orders": 0}

    # Quality Summary
    try:
        from floor_app.operations.quality.models import NonconformanceReport, QualityDisposition
        quality_summary = {
            "open_ncrs": NonconformanceReport.objects.exclude(status='CLOSED').count(),
            "dispositions": QualityDisposition.objects.count(),
        }
    except Exception:
        quality_summary = {"open_ncrs": 0, "dispositions": 0}

    # Planning Summary
    try:
        from floor_app.operations.planning.models import ProductionSchedule, KPIDefinition
        planning_summary = {
            "schedules": ProductionSchedule.objects.count(),
            "kpis": KPIDefinition.objects.filter(is_active=True).count(),
        }
    except Exception:
        planning_summary = {"schedules": 0, "kpis": 0}

    # Sales Summary
    try:
        from floor_app.operations.sales.models import Customer, SalesOpportunity, SalesOrder, DrillingRun
        sales_summary = {
            "customers": Customer.objects.filter(is_deleted=False).count(),
            "opportunities": SalesOpportunity.objects.filter(is_deleted=False).count(),
            "orders": SalesOrder.objects.filter(is_deleted=False).count(),
            "drilling_runs": DrillingRun.objects.filter(is_deleted=False).count(),
        }
    except Exception:
        sales_summary = {"customers": 0, "opportunities": 0, "orders": 0, "drilling_runs": 0}

    # Finance summary
    finance_summary = {
        "erp_references": ERPReference.objects.count(),
        "pending_sync": ERPReference.objects.filter(sync_status='pending').count(),
        "loss_events": LossOfSaleEvent.objects.count(),
        "total_loss": LossOfSaleEvent.objects.aggregate(total=Sum('estimated_loss_amount'))['total'] or 0,
    }

    context = {
        "hr_summary": hr_summary,
        "inventory_summary": inventory_summary,
        "production_summary": production_summary,
        "evaluation_summary": evaluation_summary,
        "purchasing_summary": purchasing_summary,
        "qrcodes_summary": qrcodes_summary,
        "knowledge_summary": knowledge_summary,
        "maintenance_summary": maintenance_summary,
        "quality_summary": quality_summary,
        "planning_summary": planning_summary,
        "sales_summary": sales_summary,
        "finance_summary": finance_summary,
    }

    return render(request, "core/main_dashboard.html", context)


# ============================================================================
# USER PREFERENCES
# ============================================================================

@login_required
def user_preferences(request):
    """User preferences/settings page."""
    pref = UserPreference.get_or_create_for_user(request.user)

    if request.method == 'POST':
        pref.theme = request.POST.get('theme', 'light')
        pref.font_size = request.POST.get('font_size', 'normal')
        pref.table_density = request.POST.get('table_density', 'normal')
        pref.default_landing_page = request.POST.get('default_landing_page', '')
        pref.email_notifications = request.POST.get('email_notifications') == 'on'
        pref.desktop_notifications = request.POST.get('desktop_notifications') == 'on'
        pref.save()

        messages.success(request, 'Your preferences have been saved.')
        return redirect('core:user_preferences')

    context = {
        'title': 'User Preferences',
        'preferences': pref,
        'theme_choices': UserPreference.THEME_CHOICES,
        'font_size_choices': UserPreference.FONT_SIZE_CHOICES,
        'table_density_choices': UserPreference.TABLE_DENSITY_CHOICES,
    }
    return render(request, 'core/user_preferences.html', context)


@login_required
def reset_table_columns(request):
    """Reset table column preferences."""
    if request.method == 'POST':
        pref = UserPreference.get_or_create_for_user(request.user)
        view_name = request.POST.get('view_name', '')

        if view_name:
            if view_name in pref.table_columns_config:
                del pref.table_columns_config[view_name]
        else:
            pref.table_columns_config = {}

        pref.save()
        messages.success(request, 'Column preferences have been reset.')

    return redirect('core:user_preferences')


# ============================================================================
# API ENDPOINTS
# ============================================================================

class TableColumnsAPIView(LoginRequiredMixin, View):
    """API endpoint for table column preferences."""

    def get(self, request):
        view_name = request.GET.get('view', '')
        if not view_name:
            return JsonResponse({'error': 'view parameter required'}, status=400)

        pref = UserPreference.get_or_create_for_user(request.user)
        columns = pref.get_table_columns(view_name)

        return JsonResponse({'view': view_name, 'columns': columns})

    def post(self, request):
        try:
            data = json.loads(request.body)
            view_name = data.get('view', '')
            columns = data.get('columns', [])

            if not view_name:
                return JsonResponse({'error': 'view parameter required'}, status=400)

            pref = UserPreference.get_or_create_for_user(request.user)
            pref.set_table_columns(view_name, columns)

            return JsonResponse({'success': True, 'view': view_name, 'columns': columns})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# FINANCE DASHBOARD & COST CENTER MANAGEMENT
# ============================================================================

@login_required
@user_passes_test(lambda u: u.is_staff)
def finance_dashboard(request):
    """Finance integration dashboard."""
    context = {
        'title': 'Finance Dashboard',
        'total_erp_references': ERPReference.objects.count(),
        'pending_sync': ERPReference.objects.filter(sync_status='pending').count(),
        'sync_errors': ERPReference.objects.filter(sync_status='error').count(),
        'total_loss_events': LossOfSaleEvent.objects.count(),
        'total_loss_amount': LossOfSaleEvent.objects.aggregate(total=Sum('estimated_loss_amount'))['total'] or 0,
        'document_types': ERPDocumentType.objects.annotate(ref_count=Count('references')).order_by('-ref_count')[:10],
        'recent_references': ERPReference.objects.select_related('document_type').order_by('-created_at')[:10],
        'recent_loss_events': LossOfSaleEvent.objects.select_related('cause').order_by('-event_date')[:5],
    }
    return render(request, 'core/finance_dashboard.html', context)


class CostCenterListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CostCenter
    template_name = 'core/costcenter_list.html'
    context_object_name = 'cost_centers'
    paginate_by = 25

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = CostCenter.objects.select_related('parent', 'manager')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(Q(code__icontains=search) | Q(name__icontains=search))
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        sort = self.request.GET.get('sort', 'code')
        order = self.request.GET.get('order', 'asc')
        if order == 'desc':
            sort = f'-{sort}'
        return queryset.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cost Centers'
        return context


class CostCenterDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = CostCenter
    template_name = 'core/costcenter_detail.html'

    def test_func(self):
        return self.request.user.is_staff


class CostCenterCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CostCenter
    template_name = 'core/costcenter_form.html'
    fields = ['code', 'name', 'description', 'erp_cost_center_code', 'parent', 'manager', 'annual_budget', 'currency', 'status']
    success_url = reverse_lazy('core:costcenter_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Cost Center created successfully.')
        return super().form_valid(form)


class CostCenterUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CostCenter
    template_name = 'core/costcenter_form.html'
    fields = ['code', 'name', 'description', 'erp_cost_center_code', 'parent', 'manager', 'annual_budget', 'currency', 'status']
    success_url = reverse_lazy('core:costcenter_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Cost Center updated successfully.')
        return super().form_valid(form)


# ============================================================================
# ERP REFERENCE & LOSS OF SALE VIEWS
# ============================================================================

class ERPReferenceListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = ERPReference
    template_name = 'core/erpreference_list.html'
    context_object_name = 'references'
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = ERPReference.objects.select_related('document_type', 'content_type')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(Q(erp_number__icontains=search) | Q(notes__icontains=search))
        doc_type = self.request.GET.get('document_type', '')
        if doc_type:
            queryset = queryset.filter(document_type__code=doc_type)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'ERP References'
        context['document_types'] = ERPDocumentType.objects.filter(is_active=True)
        return context


class LossOfSaleEventListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = LossOfSaleEvent
    template_name = 'core/lossofsale_list.html'
    context_object_name = 'events'
    paginate_by = 25

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = LossOfSaleEvent.objects.select_related('cause', 'cost_center', 'reported_by')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(Q(reference_number__icontains=search) | Q(title__icontains=search))
        category = self.request.GET.get('category', '')
        if category:
            queryset = queryset.filter(cause__category=category)
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-event_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Loss of Sale Events'
        context['total_events'] = self.get_queryset().count()
        context['total_loss'] = self.get_queryset().aggregate(total=Sum('estimated_loss_amount'))['total'] or 0
        return context


class LossOfSaleEventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = LossOfSaleEvent
    template_name = 'core/lossofsale_form.html'
    fields = ['title', 'cause', 'description', 'event_date', 'event_time', 'duration_hours', 'estimated_loss_amount', 'calculation_method', 'cost_center', 'affected_customer_name', 'affected_order_number', 'root_cause_analysis', 'corrective_actions', 'preventive_measures']
    success_url = reverse_lazy('core:lossofsale_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        last_event = LossOfSaleEvent.objects.order_by('-id').first()
        next_num = (last_event.id + 1) if last_event else 1
        form.instance.reference_number = f"LOS-{next_num:06d}"
        messages.success(self.request, 'Loss of Sale event created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Loss of Sale Event'
        return context


class LossOfSaleEventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = LossOfSaleEvent
    template_name = 'core/lossofsale_detail.html'

    def test_func(self):
        return self.request.user.is_staff


# ============================================================================
# DJANGO CORE TABLES VIEWS
# ============================================================================

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class UserListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = User
    template_name = 'core/django_core/user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        queryset = User.objects.all().prefetch_related('groups')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(Q(username__icontains=search) | Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search))
        is_active = self.request.GET.get('is_active', '')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        sort = self.request.GET.get('sort', 'username')
        order = self.request.GET.get('order', 'asc')
        if order == 'desc':
            sort = f'-{sort}'
        return queryset.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Users'
        return context


class UserDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = User
    template_name = 'core/django_core/user_detail.html'
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'User: {self.object.username}'
        context['user_groups'] = self.object.groups.all()
        context['user_permissions'] = self.object.user_permissions.all()
        return context


class GroupListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Group
    template_name = 'core/django_core/group_list.html'
    context_object_name = 'groups'
    paginate_by = 25

    def get_queryset(self):
        queryset = Group.objects.all().prefetch_related('permissions')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(name__icontains=search)
        sort = self.request.GET.get('sort', 'name')
        order = self.request.GET.get('order', 'asc')
        if order == 'desc':
            sort = f'-{sort}'
        return queryset.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Groups'
        return context


class GroupDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Group
    template_name = 'core/django_core/group_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Group: {self.object.name}'
        context['group_permissions'] = self.object.permissions.all().select_related('content_type')
        context['group_users'] = self.object.user_set.all()
        return context


class PermissionListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Permission
    template_name = 'core/django_core/permission_list.html'
    context_object_name = 'permissions'
    paginate_by = 50

    def get_queryset(self):
        queryset = Permission.objects.all().select_related('content_type')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(Q(codename__icontains=search) | Q(name__icontains=search))
        ct_id = self.request.GET.get('content_type', '')
        if ct_id:
            queryset = queryset.filter(content_type_id=ct_id)
        return queryset.order_by('content_type__app_label', 'codename')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Permissions'
        context['content_types'] = ContentType.objects.all().order_by('app_label', 'model')
        return context


class ContentTypeListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = ContentType
    template_name = 'core/django_core/contenttype_list.html'
    context_object_name = 'content_types'
    paginate_by = 50

    def get_queryset(self):
        queryset = ContentType.objects.all()
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(Q(app_label__icontains=search) | Q(model__icontains=search))
        app = self.request.GET.get('app_label', '')
        if app:
            queryset = queryset.filter(app_label=app)
        return queryset.order_by('app_label', 'model')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Content Types'
        context['apps'] = ContentType.objects.values_list('app_label', flat=True).distinct().order_by('app_label')
        return context


class AdminLogListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = LogEntry
    template_name = 'core/django_core/adminlog_list.html'
    context_object_name = 'log_entries'
    paginate_by = 50

    def get_queryset(self):
        queryset = LogEntry.objects.all().select_related('user', 'content_type')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(Q(object_repr__icontains=search) | Q(change_message__icontains=search))
        action = self.request.GET.get('action_flag', '')
        if action:
            queryset = queryset.filter(action_flag=action)
        user_id = self.request.GET.get('user', '')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset.order_by('-action_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Admin Log'
        context['users'] = User.objects.filter(is_staff=True)
        return context


class SessionListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Session
    template_name = 'core/django_core/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 50

    def get_queryset(self):
        from django.utils import timezone
        return Session.objects.filter(expire_date__gte=timezone.now()).order_by('-expire_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Active Sessions'
        return context


# ============================================================================
# USER CRUD VIEWS
# ============================================================================

class UserCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Create a new user"""
    model = User
    form_class = UserCreateForm
    template_name = 'core/django_core/user_form.html'
    success_url = reverse_lazy('core:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New User'
        context['action'] = 'Create'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'User "{form.cleaned_data["username"]}" created successfully!')
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Update an existing user"""
    model = User
    form_class = UserUpdateForm
    template_name = 'core/django_core/user_form.html'
    success_url = reverse_lazy('core:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit User: {self.object.username}'
        context['action'] = 'Update'
        return context

    def form_valid(self, form):
        # Check if user is trying to deactivate themselves
        if self.request.user == self.object and not form.cleaned_data.get('is_active'):
            messages.error(self.request, 'You cannot deactivate your own account!')
            return self.form_invalid(form)

        messages.success(self.request, f'User "{self.object.username}" updated successfully!')
        return super().form_valid(form)


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_password_change(request, pk):
    """Change user password (admin-initiated)"""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Password for "{user.username}" changed successfully!')
            return redirect('core:user_detail', pk=pk)
    else:
        form = UserPasswordChangeForm(user)

    return render(request, 'core/django_core/user_password_change.html', {
        'title': f'Change Password: {user.username}',
        'form': form,
        'user_obj': user,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_delete(request, pk):
    """Delete (deactivate) a user"""
    user = get_object_or_404(User, pk=pk)

    # Prevent self-deletion
    if request.user == user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('core:user_list')

    # Prevent deleting last superuser
    if user.is_superuser and User.objects.filter(is_superuser=True, is_active=True).count() == 1:
        messages.error(request, 'Cannot delete the last active superuser!')
        return redirect('core:user_list')

    if request.method == 'POST':
        # Soft delete by deactivating
        user.is_active = False
        user.save()
        messages.success(request, f'User "{user.username}" deactivated successfully!')
        return redirect('core:user_list')

    return render(request, 'core/django_core/user_confirm_delete.html', {
        'title': f'Deactivate User: {user.username}',
        'user_obj': user,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_toggle_active(request, pk):
    """Toggle user active status"""
    user = get_object_or_404(User, pk=pk)

    # Prevent self-deactivation
    if request.user == user and user.is_active:
        messages.error(request, 'You cannot deactivate your own account!')
        return redirect('core:user_detail', pk=pk)

    user.is_active = not user.is_active
    user.save()

    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User "{user.username}" {status} successfully!')
    return redirect('core:user_detail', pk=pk)


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_permissions(request, pk):
    """Manage user-specific permissions"""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserPermissionsForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Permissions for "{user.username}" updated successfully!')
            return redirect('core:user_detail', pk=pk)
    else:
        form = UserPermissionsForm(instance=user)

    # Group permissions by app and model
    permissions_by_app = {}
    for perm in Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename'):
        app_label = perm.content_type.app_label
        model = perm.content_type.model

        if app_label not in permissions_by_app:
            permissions_by_app[app_label] = {}

        if model not in permissions_by_app[app_label]:
            permissions_by_app[app_label][model] = []

        permissions_by_app[app_label][model].append(perm)

    return render(request, 'core/django_core/user_permissions.html', {
        'title': f'Manage Permissions: {user.username}',
        'form': form,
        'user_obj': user,
        'permissions_by_app': permissions_by_app,
    })


# ============================================================================
# GROUP CRUD VIEWS
# ============================================================================

class GroupCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Create a new group"""
    model = Group
    form_class = GroupForm
    template_name = 'core/django_core/group_form.html'
    success_url = reverse_lazy('core:group_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Group'
        context['action'] = 'Create'

        # Group permissions by app and model for better UX
        permissions_by_app = {}
        for perm in Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename'):
            app_label = perm.content_type.app_label
            model = perm.content_type.model

            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = {}

            if model not in permissions_by_app[app_label]:
                permissions_by_app[app_label][model] = []

            permissions_by_app[app_label][model].append(perm)

        context['permissions_by_app'] = permissions_by_app
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Group "{form.cleaned_data["name"]}" created successfully!')
        return super().form_valid(form)


class GroupUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Update an existing group"""
    model = Group
    form_class = GroupForm
    template_name = 'core/django_core/group_form.html'
    success_url = reverse_lazy('core:group_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Group: {self.object.name}'
        context['action'] = 'Update'

        # Group permissions by app and model for better UX
        permissions_by_app = {}
        for perm in Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename'):
            app_label = perm.content_type.app_label
            model = perm.content_type.model

            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = {}

            if model not in permissions_by_app[app_label]:
                permissions_by_app[app_label][model] = []

            permissions_by_app[app_label][model].append(perm)

        context['permissions_by_app'] = permissions_by_app
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Group "{self.object.name}" updated successfully!')
        return super().form_valid(form)


@login_required
@user_passes_test(lambda u: u.is_staff)
def group_delete(request, pk):
    """Delete a group"""
    group = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        group_name = group.name
        # Check if group has members
        member_count = group.user_set.count()

        if member_count > 0:
            messages.warning(request, f'Group "{group_name}" has {member_count} member(s). They will lose group permissions.')

        group.delete()
        messages.success(request, f'Group "{group_name}" deleted successfully!')
        return redirect('core:group_list')

    return render(request, 'core/django_core/group_confirm_delete.html', {
        'title': f'Delete Group: {group.name}',
        'group': group,
        'member_count': group.user_set.count(),
    })


# ============================================================================
# GLOBAL SEARCH
# ============================================================================

@login_required
def global_search(request):
    """Global search across all modules."""
    query = request.GET.get('q', '').strip()
    modules = request.GET.getlist('modules')  # Filter by specific modules

    results = []
    total_count = 0

    if query and len(query) >= 2:
        # Execute search
        search = GlobalSearch(query=query, modules=modules, limit_per_model=10)
        results = search.execute()

        # Calculate total count
        total_count = sum(r['count'] for r in results)

        # Save to search history
        SearchHistory.add_search(request.user, query, module=None)

    # Get recent searches for sidebar
    recent_searches = SearchHistory.get_recent_searches(request.user, limit=5)

    context = {
        'title': 'Global Search',
        'query': query,
        'results': results,
        'total_count': total_count,
        'selected_modules': modules,
        'recent_searches': recent_searches,
        'available_modules': ['hr', 'inventory', 'core'],
    }

    return render(request, 'core/search_results.html', context)


@login_required
def global_search_api(request):
    """AJAX API endpoint for live search autocomplete."""
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    # Execute search with lower limit for autocomplete
    search = GlobalSearch(query=query, limit_per_model=5)
    results = search.execute()

    # Format results for autocomplete
    formatted_results = []
    for model_group in results:
        for item in model_group['results']:
            formatted_results.append({
                'id': item['id'],
                'text': item['display'],
                'icon': model_group['model_icon'],
                'label': model_group['model_label'],
                'url': request.build_absolute_uri(
                    reverse(item['url_pattern'], kwargs={'pk': item['id']})
                ),
            })

    return JsonResponse({'results': formatted_results[:20]})


# Health check endpoints
from .health import health_check, readiness_check, liveness_check

