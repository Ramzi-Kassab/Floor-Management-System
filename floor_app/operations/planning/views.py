"""
Planning & KPI Management - Views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from decimal import Decimal

from .models import (
    ResourceType,
    ResourceCapacity,
    ProductionSchedule,
    ScheduledOperation,
    KPIDefinition,
    KPIValue,
    JobMetrics,
    WIPSnapshot,
    DeliveryForecast,
)
from .forms import (
    ResourceTypeForm,
    ResourceCapacityForm,
    ProductionScheduleForm,
    ScheduledOperationForm,
    KPIDefinitionForm,
    KPIValueForm,
)


@login_required
def dashboard(request):
    """Planning & KPI Management Dashboard."""
    today = timezone.now().date()

    # Schedule Stats
    active_schedule = ProductionSchedule.objects.filter(
        status='PUBLISHED'
    ).order_by('-schedule_date').first()

    schedule_stats = {
        'total_schedules': ProductionSchedule.objects.count(),
        'active': active_schedule,
        'draft': ProductionSchedule.objects.filter(status='DRAFT').count(),
    }

    # Resource Stats
    resource_stats = {
        'total_resources': ResourceType.objects.filter(is_active=True).count(),
        'bottlenecks': ResourceType.objects.filter(is_bottleneck=True).count(),
    }

    # Today's capacity utilization
    today_capacity = ResourceCapacity.objects.filter(date=today)
    avg_utilization = today_capacity.aggregate(
        avg=Avg('planned_load_hours')
    )['avg'] or 0

    # KPI Summary
    recent_kpis = KPIValue.objects.filter(
        kpi_definition__show_on_dashboard=True
    ).order_by('-period_start')[:10]

    kpi_stats = {
        'on_target': KPIValue.objects.filter(is_on_target=True).count(),
        'off_target': KPIValue.objects.filter(is_on_target=False).count(),
    }

    # WIP Stats
    latest_wip = WIPSnapshot.objects.order_by('-snapshot_time').first()

    # Delivery Forecast Stats
    at_risk_count = DeliveryForecast.objects.filter(at_risk=True).count()
    escalation_needed = DeliveryForecast.objects.filter(escalation_required=True).count()

    # Overdue operations
    overdue_operations = ScheduledOperation.objects.filter(
        status='IN_PROGRESS',
        planned_end__lt=timezone.now()
    ).count()

    context = {
        'schedule_stats': schedule_stats,
        'resource_stats': resource_stats,
        'avg_utilization': avg_utilization,
        'recent_kpis': recent_kpis,
        'kpi_stats': kpi_stats,
        'latest_wip': latest_wip,
        'at_risk_count': at_risk_count,
        'escalation_needed': escalation_needed,
        'overdue_operations': overdue_operations,
    }
    return render(request, 'planning/dashboard.html', context)


# === Resource Management ===

@login_required
def resource_list(request):
    """List all resource types."""
    resources = ResourceType.objects.all()

    category = request.GET.get('category')
    if category:
        resources = resources.filter(category=category)

    context = {
        'resources': resources,
        'category_choices': ResourceType.CATEGORY_CHOICES,
    }
    return render(request, 'planning/resource/list.html', context)


@login_required
def resource_create(request):
    """Create new resource type."""
    if request.method == 'POST':
        form = ResourceTypeForm(request.POST)
        if form.is_valid():
            resource = form.save()
            messages.success(request, f'Resource {resource.code} created.')
            return redirect('planning:resource_detail', pk=resource.pk)
    else:
        form = ResourceTypeForm()

    context = {'form': form, 'title': 'Create Resource Type'}
    return render(request, 'planning/resource/form.html', context)


@login_required
def resource_detail(request, pk):
    """View resource details."""
    resource = get_object_or_404(ResourceType, pk=pk)
    today = timezone.now().date()

    # Get capacity for next 30 days
    next_30_days = today + timedelta(days=30)
    capacity = resource.capacity_records.filter(
        date__gte=today,
        date__lte=next_30_days
    ).order_by('date')

    context = {
        'resource': resource,
        'capacity': capacity,
    }
    return render(request, 'planning/resource/detail.html', context)


@login_required
def resource_edit(request, pk):
    """Edit resource type."""
    resource = get_object_or_404(ResourceType, pk=pk)

    if request.method == 'POST':
        form = ResourceTypeForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f'Resource {resource.code} updated.')
            return redirect('planning:resource_detail', pk=resource.pk)
    else:
        form = ResourceTypeForm(instance=resource)

    context = {'form': form, 'resource': resource, 'title': f'Edit {resource.code}'}
    return render(request, 'planning/resource/form.html', context)


# === Capacity Planning ===

@login_required
def capacity_overview(request):
    """Capacity overview for all resources."""
    today = timezone.now().date()
    resources = ResourceType.objects.filter(is_active=True)

    # Get capacity for today
    capacity_data = []
    for resource in resources:
        cap = resource.capacity_records.filter(date=today).first()
        capacity_data.append({
            'resource': resource,
            'capacity': cap,
        })

    context = {
        'capacity_data': capacity_data,
        'date': today,
    }
    return render(request, 'planning/capacity/overview.html', context)


@login_required
def capacity_plan(request, resource_id):
    """Plan capacity for a specific resource."""
    resource = get_object_or_404(ResourceType, pk=resource_id)

    if request.method == 'POST':
        form = ResourceCapacityForm(request.POST)
        if form.is_valid():
            capacity = form.save(commit=False)
            capacity.resource_type = resource
            capacity.save()
            messages.success(request, 'Capacity record saved.')
            return redirect('planning:resource_detail', pk=resource.pk)
    else:
        form = ResourceCapacityForm()

    context = {'form': form, 'resource': resource}
    return render(request, 'planning/capacity/plan_form.html', context)


@login_required
def bottleneck_analysis(request):
    """Analyze bottleneck resources."""
    today = timezone.now().date()

    bottleneck_resources = ResourceType.objects.filter(is_bottleneck=True)
    overloaded = ResourceCapacity.objects.filter(
        date=today
    ).extra(
        where=['planned_load_hours > (available_hours - reserved_hours)']
    )

    context = {
        'bottleneck_resources': bottleneck_resources,
        'overloaded': overloaded,
    }
    return render(request, 'planning/capacity/bottleneck.html', context)


# === Schedule Management ===

@login_required
def schedule_list(request):
    """List all production schedules."""
    schedules = ProductionSchedule.objects.all()

    status = request.GET.get('status')
    if status:
        schedules = schedules.filter(status=status)

    paginator = Paginator(schedules, 20)
    page = request.GET.get('page')
    schedules = paginator.get_page(page)

    context = {
        'schedules': schedules,
        'status_choices': ProductionSchedule.STATUS_CHOICES,
    }
    return render(request, 'planning/schedule/list.html', context)


@login_required
def schedule_create(request):
    """Create new production schedule."""
    if request.method == 'POST':
        form = ProductionScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            messages.success(request, f'Schedule {schedule.name} created.')
            return redirect('planning:schedule_detail', pk=schedule.pk)
    else:
        form = ProductionScheduleForm()

    context = {'form': form, 'title': 'Create Schedule'}
    return render(request, 'planning/schedule/form.html', context)


@login_required
def schedule_detail(request, pk):
    """View schedule details."""
    schedule = get_object_or_404(ProductionSchedule, pk=pk)
    operations = schedule.scheduled_operations.all()[:50]

    context = {
        'schedule': schedule,
        'operations': operations,
    }
    return render(request, 'planning/schedule/detail.html', context)


@login_required
def schedule_edit(request, pk):
    """Edit production schedule."""
    schedule = get_object_or_404(ProductionSchedule, pk=pk)

    if not schedule.is_editable:
        messages.error(request, 'This schedule cannot be edited.')
        return redirect('planning:schedule_detail', pk=schedule.pk)

    if request.method == 'POST':
        form = ProductionScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, f'Schedule {schedule.name} updated.')
            return redirect('planning:schedule_detail', pk=schedule.pk)
    else:
        form = ProductionScheduleForm(instance=schedule)

    context = {'form': form, 'schedule': schedule, 'title': f'Edit {schedule.name}'}
    return render(request, 'planning/schedule/form.html', context)


@login_required
def schedule_publish(request, pk):
    """Publish a schedule."""
    schedule = get_object_or_404(ProductionSchedule, pk=pk)

    if request.method == 'POST':
        try:
            schedule.publish(request.user)
            messages.success(request, f'Schedule {schedule.name} published.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('planning:schedule_detail', pk=schedule.pk)

    context = {'schedule': schedule}
    return render(request, 'planning/schedule/publish_confirm.html', context)


@login_required
def schedule_operations(request, pk):
    """View all operations in a schedule."""
    schedule = get_object_or_404(ProductionSchedule, pk=pk)
    operations = schedule.scheduled_operations.all()

    paginator = Paginator(operations, 50)
    page = request.GET.get('page')
    operations = paginator.get_page(page)

    context = {
        'schedule': schedule,
        'operations': operations,
    }
    return render(request, 'planning/schedule/operations.html', context)


# === Scheduled Operations ===

@login_required
def operation_detail(request, pk):
    """View operation details."""
    operation = get_object_or_404(ScheduledOperation, pk=pk)

    context = {'operation': operation}
    return render(request, 'planning/schedule/operation_detail.html', context)


@login_required
def operation_start(request, pk):
    """Start an operation."""
    operation = get_object_or_404(ScheduledOperation, pk=pk)

    if request.method == 'POST':
        operation.start_operation()
        messages.success(request, 'Operation started.')
        return redirect('planning:operation_detail', pk=operation.pk)

    context = {'operation': operation}
    return render(request, 'planning/schedule/operation_start_confirm.html', context)


@login_required
def operation_complete(request, pk):
    """Complete an operation."""
    operation = get_object_or_404(ScheduledOperation, pk=pk)

    if request.method == 'POST':
        operation.complete_operation()
        messages.success(request, 'Operation completed.')
        return redirect('planning:operation_detail', pk=operation.pk)

    context = {'operation': operation}
    return render(request, 'planning/schedule/operation_complete_confirm.html', context)


# === KPI Management ===

@login_required
def kpi_dashboard(request):
    """KPI dashboard with key metrics."""
    # Get dashboard KPIs
    dashboard_kpis = KPIDefinition.objects.filter(
        show_on_dashboard=True,
        is_active=True
    )

    # Get latest values for each KPI
    kpi_data = []
    for kpi in dashboard_kpis:
        latest_value = kpi.values.order_by('-period_start').first()
        kpi_data.append({
            'definition': kpi,
            'latest_value': latest_value,
        })

    context = {'kpi_data': kpi_data}
    return render(request, 'planning/kpi/dashboard.html', context)


@login_required
def kpi_definition_list(request):
    """List all KPI definitions."""
    definitions = KPIDefinition.objects.all()

    category = request.GET.get('category')
    if category:
        definitions = definitions.filter(category=category)

    context = {
        'definitions': definitions,
        'category_choices': KPIDefinition.CATEGORY_CHOICES,
    }
    return render(request, 'planning/kpi/definition_list.html', context)


@login_required
def kpi_definition_create(request):
    """Create new KPI definition."""
    if request.method == 'POST':
        form = KPIDefinitionForm(request.POST)
        if form.is_valid():
            definition = form.save()
            messages.success(request, f'KPI {definition.code} created.')
            return redirect('planning:kpi_definition_detail', pk=definition.pk)
    else:
        form = KPIDefinitionForm()

    context = {'form': form, 'title': 'Create KPI Definition'}
    return render(request, 'planning/kpi/definition_form.html', context)


@login_required
def kpi_definition_detail(request, pk):
    """View KPI definition and values."""
    definition = get_object_or_404(KPIDefinition, pk=pk)
    values = definition.values.order_by('-period_start')[:20]

    context = {
        'definition': definition,
        'values': values,
    }
    return render(request, 'planning/kpi/definition_detail.html', context)


@login_required
def kpi_value_list(request):
    """List KPI values."""
    values = KPIValue.objects.select_related('kpi_definition').all()

    kpi_id = request.GET.get('kpi')
    if kpi_id:
        values = values.filter(kpi_definition_id=kpi_id)

    paginator = Paginator(values, 50)
    page = request.GET.get('page')
    values = paginator.get_page(page)

    context = {
        'values': values,
        'kpi_definitions': KPIDefinition.objects.filter(is_active=True),
    }
    return render(request, 'planning/kpi/value_list.html', context)


@login_required
def kpi_value_record(request):
    """Record a new KPI value."""
    if request.method == 'POST':
        form = KPIValueForm(request.POST)
        if form.is_valid():
            value = form.save()
            messages.success(request, 'KPI value recorded.')
            return redirect('planning:kpi_value_list')
    else:
        form = KPIValueForm()

    context = {'form': form}
    return render(request, 'planning/kpi/value_form.html', context)


@login_required
def kpi_trends(request):
    """View KPI trends over time."""
    # Get selected KPI
    kpi_id = request.GET.get('kpi')
    selected_kpi = None
    trend_data = []

    if kpi_id:
        selected_kpi = get_object_or_404(KPIDefinition, pk=kpi_id)
        trend_data = selected_kpi.values.order_by('period_start')

    context = {
        'kpi_definitions': KPIDefinition.objects.filter(is_active=True),
        'selected_kpi': selected_kpi,
        'trend_data': trend_data,
    }
    return render(request, 'planning/kpi/trends.html', context)


# === WIP Tracking ===

@login_required
def wip_board(request):
    """WIP board view."""
    latest_wip = WIPSnapshot.objects.order_by('-snapshot_time').first()

    context = {'wip': latest_wip}
    return render(request, 'planning/wip/board.html', context)


@login_required
def wip_snapshot(request):
    """Create WIP snapshot."""
    if request.method == 'POST':
        # In production, this would calculate actual WIP from JobCards
        snapshot = WIPSnapshot.objects.create(
            snapshot_time=timezone.now(),
            total_jobs_in_wip=0,
            jobs_on_track=0,
            jobs_at_risk=0,
            jobs_delayed=0,
        )
        messages.success(request, 'WIP snapshot created.')
        return redirect('planning:wip_board')

    return render(request, 'planning/wip/snapshot_confirm.html')


@login_required
def wip_history(request):
    """View WIP snapshot history."""
    snapshots = WIPSnapshot.objects.order_by('-snapshot_time')

    paginator = Paginator(snapshots, 20)
    page = request.GET.get('page')
    snapshots = paginator.get_page(page)

    context = {'snapshots': snapshots}
    return render(request, 'planning/wip/history.html', context)


# === Job Metrics ===

@login_required
def metrics_overview(request):
    """Job metrics overview."""
    metrics = JobMetrics.objects.all()

    # Summary stats
    total_jobs = metrics.count()
    on_time_count = metrics.filter(is_on_time=True).count()
    on_time_percentage = (on_time_count / total_jobs * 100) if total_jobs > 0 else 0

    avg_turnaround = metrics.aggregate(
        avg=Avg('total_turnaround_hours')
    )['avg'] or 0

    total_cost_variance = metrics.aggregate(
        total=Sum('cost_variance')
    )['total'] or 0

    context = {
        'total_jobs': total_jobs,
        'on_time_percentage': on_time_percentage,
        'avg_turnaround': avg_turnaround,
        'total_cost_variance': total_cost_variance,
    }
    return render(request, 'planning/metrics/overview.html', context)


@login_required
def job_metrics_detail(request, job_card_id):
    """View metrics for a specific job."""
    metrics = get_object_or_404(JobMetrics, job_card_id=job_card_id)

    context = {'metrics': metrics}
    return render(request, 'planning/metrics/job_detail.html', context)


# === Delivery Forecasting ===

@login_required
def forecast_list(request):
    """List all delivery forecasts."""
    forecasts = DeliveryForecast.objects.all()

    at_risk = request.GET.get('at_risk')
    if at_risk == 'true':
        forecasts = forecasts.filter(at_risk=True)

    paginator = Paginator(forecasts, 20)
    page = request.GET.get('page')
    forecasts = paginator.get_page(page)

    context = {'forecasts': forecasts}
    return render(request, 'planning/forecast/list.html', context)


@login_required
def at_risk_jobs(request):
    """View jobs at risk of missing delivery."""
    forecasts = DeliveryForecast.objects.filter(
        at_risk=True
    ).order_by('customer_required_date')

    context = {'forecasts': forecasts}
    return render(request, 'planning/forecast/at_risk.html', context)


@login_required
def forecast_detail(request, pk):
    """View forecast details."""
    forecast = get_object_or_404(DeliveryForecast, pk=pk)

    context = {'forecast': forecast}
    return render(request, 'planning/forecast/detail.html', context)


# === Reports ===

@login_required
def reports_dashboard(request):
    """Planning reports dashboard."""
    return render(request, 'planning/reports/dashboard.html')


@login_required
def otd_report(request):
    """On-Time Delivery report."""
    metrics = JobMetrics.objects.filter(actual_completion__isnull=False)

    total = metrics.count()
    on_time = metrics.filter(is_on_time=True).count()
    late = metrics.filter(is_on_time=False).count()

    otd_percentage = (on_time / total * 100) if total > 0 else 0

    avg_delay = metrics.filter(delay_days__gt=0).aggregate(
        avg=Avg('delay_days')
    )['avg'] or 0

    context = {
        'total': total,
        'on_time': on_time,
        'late': late,
        'otd_percentage': otd_percentage,
        'avg_delay': avg_delay,
    }
    return render(request, 'planning/reports/otd.html', context)


@login_required
def utilization_report(request):
    """Resource utilization report."""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    capacity_data = ResourceCapacity.objects.filter(
        date__gte=last_30_days,
        date__lte=today
    ).values('resource_type__code').annotate(
        avg_utilization=Avg('planned_load_hours'),
        total_available=Sum('available_hours'),
    )

    context = {'capacity_data': capacity_data}
    return render(request, 'planning/reports/utilization.html', context)


# === Settings ===

@login_required
def settings_dashboard(request):
    """Planning settings dashboard."""
    resource_types = ResourceType.objects.all()
    kpi_definitions = KPIDefinition.objects.all()

    context = {
        'resource_types': resource_types,
        'kpi_definitions': kpi_definitions,
    }
    return render(request, 'planning/settings/dashboard.html', context)
