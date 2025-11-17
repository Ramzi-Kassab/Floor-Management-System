"""
Views for Maintenance & Asset Management module.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q, Avg
from django.core.paginator import Paginator
from datetime import timedelta
import json

from .models import (
    AssetCategory, AssetLocation, Asset, AssetDocument,
    PMPlan, PMSchedule, PMTask,
    MaintenanceRequest, WorkOrder, WorkOrderAttachment,
    DowntimeEvent, ProductionImpact, LostSales,
    PartsUsage,
)
from .forms import (
    AssetForm, AssetDocumentForm,
    MaintenanceRequestForm, WorkOrderForm,
    DowntimeEventForm, PMTaskCompleteForm,
)


# =============================================================================
# DASHBOARD
# =============================================================================

@login_required
def dashboard(request):
    """Main maintenance dashboard with key metrics."""
    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Asset metrics
    total_assets = Asset.objects.filter(is_deleted=False).count()
    assets_in_service = Asset.objects.filter(is_deleted=False, status='IN_SERVICE').count()
    assets_under_maintenance = Asset.objects.filter(is_deleted=False, status='UNDER_MAINTENANCE').count()
    critical_assets = Asset.objects.filter(is_deleted=False, is_critical_production_asset=True).count()

    # Work order metrics
    open_work_orders = WorkOrder.objects.filter(
        is_deleted=False,
        status__in=['PLANNED', 'ASSIGNED', 'IN_PROGRESS', 'WAITING_PARTS', 'WAITING_VENDOR']
    ).count()
    overdue_work_orders = WorkOrder.objects.filter(
        is_deleted=False,
        status__in=['PLANNED', 'ASSIGNED', 'IN_PROGRESS'],
        planned_end__lt=timezone.now()
    ).count()

    # PM metrics
    overdue_pm_tasks = PMTask.objects.filter(
        is_deleted=False,
        status__in=['SCHEDULED', 'IN_PROGRESS'],
        scheduled_date__lt=today
    ).count()
    pm_due_this_week = PMTask.objects.filter(
        is_deleted=False,
        status='SCHEDULED',
        scheduled_date__range=[today, today + timedelta(days=7)]
    ).count()

    # Downtime metrics (this month)
    total_downtime_minutes = DowntimeEvent.objects.filter(
        is_deleted=False,
        start_time__gte=month_start
    ).aggregate(total=Sum('duration_minutes'))['total'] or 0
    total_downtime_hours = round(total_downtime_minutes / 60, 1)

    # Lost sales this month
    lost_sales_total = LostSales.objects.filter(
        is_deleted=False,
        created_at__gte=month_start
    ).aggregate(total=Sum('lost_or_delayed_revenue'))['total'] or 0

    # Pending requests
    pending_requests = MaintenanceRequest.objects.filter(
        is_deleted=False,
        status='NEW'
    ).count()

    # Recent work orders
    recent_work_orders = WorkOrder.objects.filter(
        is_deleted=False
    ).select_related('asset').order_by('-created_at')[:10]

    # Top 5 assets by downtime (this month)
    top_downtime_assets = DowntimeEvent.objects.filter(
        is_deleted=False,
        start_time__gte=month_start
    ).values(
        'asset__asset_code', 'asset__name'
    ).annotate(
        total_minutes=Sum('duration_minutes')
    ).order_by('-total_minutes')[:5]

    # Work orders by status
    wo_by_status = WorkOrder.objects.filter(
        is_deleted=False
    ).exclude(
        status__in=['COMPLETED', 'CANCELLED']
    ).values('status').annotate(count=Count('id')).order_by('status')

    context = {
        'total_assets': total_assets,
        'assets_in_service': assets_in_service,
        'assets_under_maintenance': assets_under_maintenance,
        'critical_assets': critical_assets,
        'open_work_orders': open_work_orders,
        'overdue_work_orders': overdue_work_orders,
        'overdue_pm_tasks': overdue_pm_tasks,
        'pm_due_this_week': pm_due_this_week,
        'total_downtime_hours': total_downtime_hours,
        'lost_sales_total': lost_sales_total,
        'pending_requests': pending_requests,
        'recent_work_orders': recent_work_orders,
        'top_downtime_assets': top_downtime_assets,
        'wo_by_status': wo_by_status,
    }

    return render(request, 'maintenance/dashboard.html', context)


# =============================================================================
# ASSET MANAGEMENT
# =============================================================================

class AssetListView(LoginRequiredMixin, ListView):
    """List all assets with filtering."""
    model = Asset
    template_name = 'maintenance/asset/list.html'
    context_object_name = 'assets'
    paginate_by = 25

    def get_queryset(self):
        queryset = Asset.objects.filter(is_deleted=False).select_related('category', 'location')

        # Filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        criticality = self.request.GET.get('criticality')
        if criticality:
            queryset = queryset.filter(criticality=criticality)

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(location_id=location)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(asset_code__icontains=search) |
                Q(name__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(manufacturer__icontains=search)
            )

        return queryset.order_by('asset_code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = AssetCategory.objects.filter(is_deleted=False)
        context['locations'] = AssetLocation.objects.filter(is_deleted=False)
        context['status_choices'] = Asset.STATUS_CHOICES
        context['criticality_choices'] = Asset.CRITICALITY_CHOICES
        return context


class AssetDetailView(LoginRequiredMixin, DetailView):
    """Asset detail view with related information."""
    model = Asset
    template_name = 'maintenance/asset/detail.html'
    context_object_name = 'asset'

    def get_queryset(self):
        return Asset.objects.filter(is_deleted=False).select_related('category', 'location')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.object

        # Get related data
        context['documents'] = asset.documents.filter(is_deleted=False)
        context['open_work_orders'] = asset.work_orders.filter(
            is_deleted=False,
            status__in=['PLANNED', 'ASSIGNED', 'IN_PROGRESS', 'WAITING_PARTS', 'WAITING_VENDOR']
        ).order_by('-created_at')[:10]
        context['recent_downtime'] = asset.downtime_events.filter(
            is_deleted=False
        ).order_by('-start_time')[:10]
        context['pm_schedules'] = asset.pm_schedules.filter(is_deleted=False, is_active=True)

        return context


class AssetCreateView(LoginRequiredMixin, CreateView):
    """Create a new asset."""
    model = Asset
    form_class = AssetForm
    template_name = 'maintenance/asset/form.html'
    success_url = reverse_lazy('maintenance:asset_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Asset created successfully.')
        return super().form_valid(form)


class AssetUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing asset."""
    model = Asset
    form_class = AssetForm
    template_name = 'maintenance/asset/form.html'

    def get_queryset(self):
        return Asset.objects.filter(is_deleted=False)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Asset updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('maintenance:asset_detail', kwargs={'pk': self.object.pk})


@login_required
def asset_qr_generate(request, pk):
    """Generate QR code for asset."""
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)

    # Generate QR code image (simplified - would use qrcode library)
    qr_url = request.build_absolute_uri(
        reverse('maintenance:asset_scan', kwargs={'token': asset.qr_token})
    )

    context = {
        'asset': asset,
        'qr_url': qr_url,
    }

    return render(request, 'maintenance/asset/qr_generate.html', context)


@login_required
def asset_scan(request, token):
    """Landing page when QR code is scanned."""
    asset = get_object_or_404(Asset, qr_token=token, is_deleted=False)

    context = {
        'asset': asset,
    }

    return render(request, 'maintenance/asset/scan_landing.html', context)


# =============================================================================
# MAINTENANCE REQUESTS
# =============================================================================

class MaintenanceRequestListView(LoginRequiredMixin, ListView):
    """List all maintenance requests."""
    model = MaintenanceRequest
    template_name = 'maintenance/corrective/request_list.html'
    context_object_name = 'requests'
    paginate_by = 25

    def get_queryset(self):
        queryset = MaintenanceRequest.objects.filter(
            is_deleted=False
        ).select_related('asset', 'requested_by')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.order_by('-request_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = MaintenanceRequest.STATUS_CHOICES
        context['priority_choices'] = MaintenanceRequest.PRIORITY_CHOICES
        return context


class MaintenanceRequestCreateView(LoginRequiredMixin, CreateView):
    """Create a new maintenance request."""
    model = MaintenanceRequest
    form_class = MaintenanceRequestForm
    template_name = 'maintenance/corrective/request_form.html'
    success_url = reverse_lazy('maintenance:request_list')

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        form.instance.created_by = self.request.user

        # Auto-generate request number
        today = timezone.now()
        year = today.year
        last_request = MaintenanceRequest.objects.filter(
            request_number__startswith=f'REQ-{year}-'
        ).order_by('-request_number').first()

        if last_request:
            last_num = int(last_request.request_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        form.instance.request_number = f'REQ-{year}-{new_num:04d}'

        messages.success(self.request, f'Request {form.instance.request_number} created successfully.')
        return super().form_valid(form)


@login_required
def request_approve(request, pk):
    """Approve a maintenance request."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    req = get_object_or_404(MaintenanceRequest, pk=pk, is_deleted=False)
    req.approve(request.user)
    messages.success(request, f'Request {req.request_number} approved.')
    return redirect('maintenance:request_list')


@login_required
def request_reject(request, pk):
    """Reject a maintenance request."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    req = get_object_or_404(MaintenanceRequest, pk=pk, is_deleted=False)
    reason = request.POST.get('reason', '')
    req.reject(request.user, reason)
    messages.warning(request, f'Request {req.request_number} rejected.')
    return redirect('maintenance:request_list')


@login_required
def request_convert_to_wo(request, pk):
    """Convert approved request to work order."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    req = get_object_or_404(MaintenanceRequest, pk=pk, is_deleted=False, status='APPROVED')

    # Generate WO number
    today = timezone.now()
    year = today.year
    last_wo = WorkOrder.objects.filter(
        wo_number__startswith=f'WO-{year}-'
    ).order_by('-wo_number').first()

    if last_wo:
        last_num = int(last_wo.wo_number.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    wo_number = f'WO-{year}-{new_num:04d}'

    # Create work order
    wo = WorkOrder.objects.create(
        wo_number=wo_number,
        asset=req.asset,
        wo_type='CORRECTIVE',
        priority=req.priority,
        title=req.title,
        problem_description=req.description,
        created_by=request.user,
    )

    # Link request to WO
    req.work_order = wo
    req.status = 'CONVERTED'
    req.save(update_fields=['work_order', 'status', 'updated_at'])

    messages.success(request, f'Work Order {wo_number} created from request.')
    return redirect('maintenance:work_order_detail', pk=wo.pk)


# =============================================================================
# WORK ORDERS
# =============================================================================

class WorkOrderListView(LoginRequiredMixin, ListView):
    """List all work orders."""
    model = WorkOrder
    template_name = 'maintenance/corrective/wo_list.html'
    context_object_name = 'work_orders'
    paginate_by = 25

    def get_queryset(self):
        queryset = WorkOrder.objects.filter(
            is_deleted=False
        ).select_related('asset', 'assigned_to')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        wo_type = self.request.GET.get('type')
        if wo_type:
            queryset = queryset.filter(wo_type=wo_type)

        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = WorkOrder.STATUS_CHOICES
        context['type_choices'] = WorkOrder.TYPE_CHOICES
        context['priority_choices'] = WorkOrder.PRIORITY_CHOICES
        return context


class WorkOrderDetailView(LoginRequiredMixin, DetailView):
    """Work order detail view."""
    model = WorkOrder
    template_name = 'maintenance/corrective/wo_detail.html'
    context_object_name = 'work_order'

    def get_queryset(self):
        return WorkOrder.objects.filter(is_deleted=False).select_related('asset', 'assigned_to')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wo = self.object
        context['attachments'] = wo.attachments.filter(is_deleted=False)
        context['parts_used'] = wo.parts_used.filter(is_deleted=False)
        context['downtime_events'] = wo.downtime_events.filter(is_deleted=False)
        return context


class WorkOrderCreateView(LoginRequiredMixin, CreateView):
    """Create a new work order."""
    model = WorkOrder
    form_class = WorkOrderForm
    template_name = 'maintenance/corrective/wo_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        # Auto-generate WO number
        today = timezone.now()
        year = today.year
        last_wo = WorkOrder.objects.filter(
            wo_number__startswith=f'WO-{year}-'
        ).order_by('-wo_number').first()

        if last_wo:
            last_num = int(last_wo.wo_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        form.instance.wo_number = f'WO-{year}-{new_num:04d}'

        messages.success(self.request, f'Work Order {form.instance.wo_number} created.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('maintenance:work_order_detail', kwargs={'pk': self.object.pk})


@login_required
def work_order_start(request, pk):
    """Start work on a work order."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    wo = get_object_or_404(WorkOrder, pk=pk, is_deleted=False)
    wo.start_work()
    messages.success(request, f'Work started on {wo.wo_number}.')
    return redirect('maintenance:work_order_detail', pk=pk)


@login_required
def work_order_complete(request, pk):
    """Complete a work order."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    wo = get_object_or_404(WorkOrder, pk=pk, is_deleted=False)
    solution = request.POST.get('solution', '')
    actions = request.POST.get('actions', '')
    wo.complete_work(request.user, solution, actions)
    messages.success(request, f'Work Order {wo.wo_number} completed.')
    return redirect('maintenance:work_order_detail', pk=pk)


# =============================================================================
# PREVENTIVE MAINTENANCE
# =============================================================================

class PMPlanListView(LoginRequiredMixin, ListView):
    """List all PM plans."""
    model = PMPlan
    template_name = 'maintenance/preventive/plan_list.html'
    context_object_name = 'plans'
    paginate_by = 25

    def get_queryset(self):
        return PMPlan.objects.filter(is_deleted=False).order_by('code')


class PMTaskListView(LoginRequiredMixin, ListView):
    """List PM tasks."""
    model = PMTask
    template_name = 'maintenance/preventive/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 25

    def get_queryset(self):
        queryset = PMTask.objects.filter(
            is_deleted=False
        ).select_related('schedule', 'schedule__asset', 'schedule__pm_plan')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('scheduled_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = PMTask.STATUS_CHOICES
        return context


@login_required
def pm_calendar(request):
    """PM calendar view."""
    today = timezone.now().date()

    # Get PM tasks for the current month
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    tasks = PMTask.objects.filter(
        is_deleted=False,
        scheduled_date__range=[month_start, month_end]
    ).select_related('schedule__asset', 'schedule__pm_plan').order_by('scheduled_date')

    context = {
        'tasks': tasks,
        'today': today,
        'month_start': month_start,
        'month_end': month_end,
    }

    return render(request, 'maintenance/preventive/calendar.html', context)


@login_required
def pm_task_start(request, pk):
    """Start a PM task."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    task = get_object_or_404(PMTask, pk=pk, is_deleted=False)
    task.start_task(request.user)
    messages.success(request, f'PM Task {task.task_number} started.')
    return redirect('maintenance:pm_task_list')


@login_required
def pm_task_complete(request, pk):
    """Complete a PM task."""
    task = get_object_or_404(PMTask, pk=pk, is_deleted=False)

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        issues = request.POST.get('issues', '')
        follow_up = request.POST.get('follow_up') == 'on'
        task.complete_task(notes, issues, follow_up)
        messages.success(request, f'PM Task {task.task_number} completed.')
        return redirect('maintenance:pm_task_list')

    return render(request, 'maintenance/preventive/task_complete.html', {'task': task})


# =============================================================================
# DOWNTIME TRACKING
# =============================================================================

class DowntimeListView(LoginRequiredMixin, ListView):
    """List downtime events."""
    model = DowntimeEvent
    template_name = 'maintenance/downtime/list.html'
    context_object_name = 'events'
    paginate_by = 25

    def get_queryset(self):
        queryset = DowntimeEvent.objects.filter(
            is_deleted=False
        ).select_related('asset', 'work_order')

        downtime_type = self.request.GET.get('type')
        if downtime_type:
            queryset = queryset.filter(downtime_type=downtime_type)

        reason = self.request.GET.get('reason')
        if reason:
            queryset = queryset.filter(reason_category=reason)

        return queryset.order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_choices'] = DowntimeEvent.DOWNTIME_TYPE_CHOICES
        context['reason_choices'] = DowntimeEvent.REASON_CATEGORY_CHOICES
        return context


class DowntimeCreateView(LoginRequiredMixin, CreateView):
    """Record a new downtime event."""
    model = DowntimeEvent
    form_class = DowntimeEventForm
    template_name = 'maintenance/downtime/form.html'
    success_url = reverse_lazy('maintenance:downtime_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.reported_by = self.request.user
        messages.success(self.request, 'Downtime event recorded.')
        return super().form_valid(form)


@login_required
def downtime_end(request, pk):
    """End a downtime event."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    event = get_object_or_404(DowntimeEvent, pk=pk, is_deleted=False)
    event.end_downtime()
    messages.success(request, 'Downtime ended.')
    return redirect('maintenance:downtime_list')


@login_required
def lost_sales_list(request):
    """List lost sales records."""
    records = LostSales.objects.filter(
        is_deleted=False
    ).select_related('downtime_event').order_by('-created_at')

    # Summary
    total_lost = records.aggregate(total=Sum('lost_or_delayed_revenue'))['total'] or 0

    paginator = Paginator(records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_lost': total_lost,
    }

    return render(request, 'maintenance/downtime/lost_sales.html', context)


# =============================================================================
# SETTINGS
# =============================================================================

@login_required
def settings_dashboard(request):
    """Maintenance settings dashboard."""
    context = {
        'category_count': AssetCategory.objects.filter(is_deleted=False).count(),
        'location_count': AssetLocation.objects.filter(is_deleted=False).count(),
        'pm_plan_count': PMPlan.objects.filter(is_deleted=False).count(),
    }
    return render(request, 'maintenance/settings/dashboard.html', context)


class CategoryListView(LoginRequiredMixin, ListView):
    """List asset categories."""
    model = AssetCategory
    template_name = 'maintenance/settings/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return AssetCategory.objects.filter(is_deleted=False).order_by('sort_order', 'code')


class LocationListView(LoginRequiredMixin, ListView):
    """List asset locations."""
    model = AssetLocation
    template_name = 'maintenance/settings/location_list.html'
    context_object_name = 'locations'

    def get_queryset(self):
        return AssetLocation.objects.filter(is_deleted=False).order_by('sort_order', 'code')


# =============================================================================
# API / JSON ENDPOINTS
# =============================================================================

@login_required
def api_dashboard_stats(request):
    """Return dashboard statistics as JSON."""
    today = timezone.now().date()
    month_start = today.replace(day=1)

    data = {
        'total_assets': Asset.objects.filter(is_deleted=False).count(),
        'open_work_orders': WorkOrder.objects.filter(
            is_deleted=False,
            status__in=['PLANNED', 'ASSIGNED', 'IN_PROGRESS']
        ).count(),
        'overdue_pm_tasks': PMTask.objects.filter(
            is_deleted=False,
            status='SCHEDULED',
            scheduled_date__lt=today
        ).count(),
        'total_downtime_hours': round(
            (DowntimeEvent.objects.filter(
                is_deleted=False,
                start_time__gte=month_start
            ).aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60, 1
        ),
    }

    return JsonResponse(data)
