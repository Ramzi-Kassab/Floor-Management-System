"""
Views for Maintenance module.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Asset, AssetCategory, AssetLocation, AssetDocument,
    PMTemplate, PMSchedule, PMTask,
    MaintenanceRequest, WorkOrder, WorkOrderNote, WorkOrderPart,
    DowntimeEvent, ProductionImpact, LostSalesRecord
)
from .forms import (
    AssetForm, AssetSearchForm, MaintenanceRequestForm, RequestReviewForm,
    WorkOrderForm, WorkOrderAssignForm, WorkOrderCompleteForm,
    WorkOrderNoteForm, WorkOrderPartForm,
    PMTemplateForm, PMTaskCompleteForm,
    DowntimeEventForm, ProductionImpactForm, LostSalesRecordForm,
    DateRangeForm
)
from .services import MaintenanceService, DowntimeService, AssetService


# ==================== DASHBOARD ====================

@login_required
def dashboard(request):
    """Main maintenance dashboard."""
    stats = MaintenanceService.get_dashboard_stats()
    recent_work_orders = MaintenanceService.get_recent_work_orders(limit=10)
    assets_by_status = MaintenanceService.get_assets_by_status()

    # Upcoming PMs (next 7 days)
    today = timezone.now().date()
    upcoming_pms = PMSchedule.objects.filter(
        is_active=True,
        next_due_date__gte=today,
        next_due_date__lte=today + timezone.timedelta(days=7)
    ).select_related('asset', 'pm_template').order_by('next_due_date')[:10]

    # Overdue PMs
    overdue_pms = PMSchedule.objects.filter(
        is_active=True,
        next_due_date__lt=today
    ).select_related('asset', 'pm_template').order_by('next_due_date')[:10]

    context = {
        'stats': stats,
        'recent_work_orders': recent_work_orders,
        'assets_by_status': assets_by_status,
        'upcoming_pms': upcoming_pms,
        'overdue_pms': overdue_pms,
    }
    return render(request, 'maintenance/dashboard.html', context)


# ==================== ASSET VIEWS ====================

@login_required
def asset_list(request):
    """List all assets with filtering."""
    form = AssetSearchForm(request.GET)
    assets = Asset.objects.filter(is_deleted=False).select_related('category', 'location')

    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        location = form.cleaned_data.get('location')
        status = form.cleaned_data.get('status')
        criticality = form.cleaned_data.get('criticality')

        if query:
            assets = assets.filter(
                Q(asset_code__icontains=query) |
                Q(name__icontains=query) |
                Q(serial_number__icontains=query)
            )
        if category:
            assets = assets.filter(category=category)
        if location:
            assets = assets.filter(location=location)
        if status:
            assets = assets.filter(status=status)
        if criticality:
            assets = assets.filter(criticality=criticality)

    assets = assets.order_by('asset_code')
    paginator = Paginator(assets, 25)
    page = request.GET.get('page')
    assets_page = paginator.get_page(page)

    context = {
        'assets': assets_page,
        'form': form,
    }
    return render(request, 'maintenance/asset_list.html', context)


@login_required
def asset_detail(request, asset_code):
    """View asset details."""
    asset = get_object_or_404(Asset, asset_code=asset_code, is_deleted=False)

    # Get related data
    work_orders = asset.work_orders.filter(is_deleted=False).order_by('-created_at')[:10]
    pm_schedules = asset.pm_schedules.all()
    downtime_events = asset.downtime_events.all().order_by('-start_time')[:10]
    documents = asset.documents.all()

    # Health score
    health_score = AssetService.get_asset_health_score(asset)

    context = {
        'asset': asset,
        'work_orders': work_orders,
        'pm_schedules': pm_schedules,
        'downtime_events': downtime_events,
        'documents': documents,
        'health_score': health_score,
    }
    return render(request, 'maintenance/asset_detail.html', context)


@login_required
@permission_required('maintenance.add_asset', raise_exception=True)
def asset_create(request):
    """Create new asset."""
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.created_by = request.user
            asset.save()
            # Generate QR token
            AssetService.generate_qr_token(asset)
            messages.success(request, f'Asset {asset.asset_code} created successfully.')
            return redirect('maintenance:asset_detail', asset_code=asset.asset_code)
    else:
        form = AssetForm()

    return render(request, 'maintenance/asset_form.html', {'form': form, 'title': 'Create Asset'})


@login_required
@permission_required('maintenance.change_asset', raise_exception=True)
def asset_edit(request, asset_code):
    """Edit existing asset."""
    asset = get_object_or_404(Asset, asset_code=asset_code, is_deleted=False)

    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.updated_by = request.user
            asset.save()
            messages.success(request, f'Asset {asset.asset_code} updated successfully.')
            return redirect('maintenance:asset_detail', asset_code=asset.asset_code)
    else:
        form = AssetForm(instance=asset)

    return render(request, 'maintenance/asset_form.html', {'form': form, 'asset': asset, 'title': 'Edit Asset'})


@login_required
def asset_qr(request, qr_token):
    """QR code scan handler."""
    asset = get_object_or_404(Asset, qr_token=qr_token, is_deleted=False)
    return redirect('maintenance:asset_detail', asset_code=asset.asset_code)


# ==================== MAINTENANCE REQUEST VIEWS ====================

@login_required
def request_list(request):
    """List maintenance requests."""
    status_filter = request.GET.get('status', '')
    requests_qs = MaintenanceRequest.objects.filter(
        is_deleted=False
    ).select_related('asset', 'requested_by', 'reviewed_by').order_by('-created_at')

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    paginator = Paginator(requests_qs, 20)
    page = request.GET.get('page')
    requests_page = paginator.get_page(page)

    context = {
        'requests': requests_page,
        'status_filter': status_filter,
    }
    return render(request, 'maintenance/request_list.html', context)


@login_required
def request_detail(request, pk):
    """View maintenance request details."""
    req = get_object_or_404(MaintenanceRequest, pk=pk, is_deleted=False)
    return render(request, 'maintenance/request_detail.html', {'request_obj': req})


@login_required
def request_create(request):
    """Create maintenance request."""
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, user=request.user)
        if form.is_valid():
            req = form.save()
            messages.success(request, f'Maintenance request {req.request_number} created successfully.')
            return redirect('maintenance:request_detail', pk=req.pk)
    else:
        form = MaintenanceRequestForm(user=request.user)

    return render(request, 'maintenance/request_form.html', {'form': form})


@login_required
@permission_required('maintenance.can_approve_request', raise_exception=True)
def request_review(request, pk):
    """Review and approve/reject maintenance request."""
    req = get_object_or_404(MaintenanceRequest, pk=pk, is_deleted=False)

    if req.status not in ['NEW', 'UNDER_REVIEW']:
        messages.error(request, 'This request has already been processed.')
        return redirect('maintenance:request_detail', pk=pk)

    if request.method == 'POST':
        form = RequestReviewForm(request.POST, instance=req)
        if form.is_valid():
            req = form.save(commit=False)
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()

            if req.status == 'APPROVED':
                messages.success(request, 'Request approved. You can now convert it to a work order.')
            elif req.status == 'REJECTED':
                messages.warning(request, 'Request rejected.')

            return redirect('maintenance:request_detail', pk=pk)
    else:
        form = RequestReviewForm(instance=req)

    return render(request, 'maintenance/request_review.html', {'form': form, 'request_obj': req})


@login_required
@permission_required('maintenance.add_maintenanceworkorder', raise_exception=True)
def request_convert_to_wo(request, pk):
    """Convert approved request to work order."""
    req = get_object_or_404(MaintenanceRequest, pk=pk, is_deleted=False)

    if req.status != 'APPROVED':
        messages.error(request, 'Only approved requests can be converted to work orders.')
        return redirect('maintenance:request_detail', pk=pk)

    try:
        work_order = MaintenanceService.convert_request_to_work_order(req, user=request.user)
        messages.success(request, f'Work order {work_order.work_order_number} created successfully.')
        return redirect('maintenance:workorder_detail', wo_number=work_order.work_order_number)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('maintenance:request_detail', pk=pk)


# ==================== WORK ORDER VIEWS ====================

@login_required
def workorder_list(request):
    """List work orders."""
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')

    work_orders = WorkOrder.objects.filter(
        is_deleted=False
    ).select_related('asset', 'assigned_to').order_by('-created_at')

    if status_filter:
        work_orders = work_orders.filter(status=status_filter)
    if type_filter:
        work_orders = work_orders.filter(work_order_type=type_filter)

    paginator = Paginator(work_orders, 20)
    page = request.GET.get('page')
    work_orders_page = paginator.get_page(page)

    context = {
        'work_orders': work_orders_page,
        'status_filter': status_filter,
        'type_filter': type_filter,
    }
    return render(request, 'maintenance/workorder_list.html', context)


@login_required
def workorder_detail(request, wo_number):
    """View work order details."""
    work_order = get_object_or_404(
        WorkOrder, work_order_number=wo_number, is_deleted=False
    )

    notes = work_order.notes.all().order_by('-created_at')
    parts = work_order.parts_used.all()
    downtime_events = work_order.downtime_events.all()

    # Forms for adding notes and parts
    note_form = WorkOrderNoteForm()
    part_form = WorkOrderPartForm()

    context = {
        'work_order': work_order,
        'notes': notes,
        'parts': parts,
        'downtime_events': downtime_events,
        'note_form': note_form,
        'part_form': part_form,
    }
    return render(request, 'maintenance/workorder_detail.html', context)


@login_required
@permission_required('maintenance.add_maintenanceworkorder', raise_exception=True)
def workorder_create(request):
    """Create new work order."""
    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.created_by = request.user
            wo.save()
            messages.success(request, f'Work order {wo.work_order_number} created successfully.')
            return redirect('maintenance:workorder_detail', wo_number=wo.work_order_number)
    else:
        form = WorkOrderForm()

    return render(request, 'maintenance/workorder_form.html', {'form': form, 'title': 'Create Work Order'})


@login_required
@permission_required('maintenance.change_maintenanceworkorder', raise_exception=True)
def workorder_edit(request, wo_number):
    """Edit work order."""
    work_order = get_object_or_404(
        WorkOrder, work_order_number=wo_number, is_deleted=False
    )

    if request.method == 'POST':
        form = WorkOrderForm(request.POST, instance=work_order)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.updated_by = request.user
            wo.save()
            messages.success(request, f'Work order {wo.work_order_number} updated successfully.')
            return redirect('maintenance:workorder_detail', wo_number=wo.work_order_number)
    else:
        form = WorkOrderForm(instance=work_order)

    return render(request, 'maintenance/workorder_form.html', {
        'form': form,
        'work_order': work_order,
        'title': 'Edit Work Order'
    })


@login_required
@permission_required('maintenance.can_assign_workorder', raise_exception=True)
def workorder_assign(request, wo_number):
    """Assign work order to technician."""
    work_order = get_object_or_404(
        WorkOrder, work_order_number=wo_number, is_deleted=False
    )

    if request.method == 'POST':
        form = WorkOrderAssignForm(request.POST, instance=work_order)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.assigned_by = request.user
            wo.assigned_at = timezone.now()
            wo.status = 'ASSIGNED'
            wo.save()
            messages.success(request, f'Work order assigned successfully.')
            return redirect('maintenance:workorder_detail', wo_number=wo.work_order_number)
    else:
        form = WorkOrderAssignForm(instance=work_order)

    return render(request, 'maintenance/workorder_assign.html', {
        'form': form,
        'work_order': work_order
    })


@login_required
@permission_required('maintenance.can_complete_workorder', raise_exception=True)
def workorder_complete(request, wo_number):
    """Complete work order."""
    work_order = get_object_or_404(
        WorkOrder, work_order_number=wo_number, is_deleted=False
    )

    if request.method == 'POST':
        form = WorkOrderCompleteForm(request.POST, instance=work_order)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.status = 'COMPLETED'
            wo.completed_by = request.user
            wo.completed_at = timezone.now()
            wo.save()
            messages.success(request, f'Work order {wo.work_order_number} completed successfully.')
            return redirect('maintenance:workorder_detail', wo_number=wo.work_order_number)
    else:
        form = WorkOrderCompleteForm(instance=work_order)

    return render(request, 'maintenance/workorder_complete.html', {
        'form': form,
        'work_order': work_order
    })


@login_required
@require_POST
def workorder_add_note(request, wo_number):
    """Add note to work order."""
    work_order = get_object_or_404(
        WorkOrder, work_order_number=wo_number, is_deleted=False
    )

    form = WorkOrderNoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.work_order = work_order
        note.created_by = request.user
        note.save()
        messages.success(request, 'Note added successfully.')
    else:
        messages.error(request, 'Invalid note data.')

    return redirect('maintenance:workorder_detail', wo_number=wo_number)


@login_required
@require_POST
def workorder_add_part(request, wo_number):
    """Add part to work order."""
    work_order = get_object_or_404(
        WorkOrder, work_order_number=wo_number, is_deleted=False
    )

    form = WorkOrderPartForm(request.POST)
    if form.is_valid():
        part = form.save(commit=False)
        part.work_order = work_order
        part.save()
        messages.success(request, 'Part added successfully.')
    else:
        messages.error(request, 'Invalid part data.')

    return redirect('maintenance:workorder_detail', wo_number=wo_number)


# ==================== PM VIEWS ====================

@login_required
def pm_calendar(request):
    """PM calendar view."""
    today = timezone.now().date()

    # Get all active schedules
    schedules = PMSchedule.objects.filter(
        is_active=True
    ).select_related('asset', 'pm_template').order_by('next_due_date')

    # Split into overdue, this week, this month
    overdue = []
    this_week = []
    this_month = []
    future = []

    week_end = today + timezone.timedelta(days=7)
    month_end = today + timezone.timedelta(days=30)

    for schedule in schedules:
        if schedule.next_due_date < today:
            overdue.append(schedule)
        elif schedule.next_due_date <= week_end:
            this_week.append(schedule)
        elif schedule.next_due_date <= month_end:
            this_month.append(schedule)
        else:
            future.append(schedule)

    context = {
        'overdue': overdue,
        'this_week': this_week,
        'this_month': this_month,
        'future': future[:20],  # Limit future items
    }
    return render(request, 'maintenance/pm_calendar.html', context)


@login_required
def pm_template_list(request):
    """List PM templates."""
    templates = PMTemplate.objects.all().order_by('code')
    return render(request, 'maintenance/pm_template_list.html', {'templates': templates})


@login_required
def pm_task_list(request):
    """List PM tasks."""
    status_filter = request.GET.get('status', '')

    tasks = PMTask.objects.filter(
        is_deleted=False
    ).select_related('schedule__asset', 'schedule__pm_template', 'performed_by').order_by('-scheduled_date')

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    paginator = Paginator(tasks, 20)
    page = request.GET.get('page')
    tasks_page = paginator.get_page(page)

    context = {
        'tasks': tasks_page,
        'status_filter': status_filter,
    }
    return render(request, 'maintenance/pm_task_list.html', context)


@login_required
def pm_task_detail(request, pk):
    """View PM task details."""
    task = get_object_or_404(PMTask, pk=pk, is_deleted=False)
    return render(request, 'maintenance/pm_task_detail.html', {'task': task})


@login_required
@permission_required('maintenance.change_pmtask', raise_exception=True)
def pm_task_complete(request, pk):
    """Complete a PM task."""
    task = get_object_or_404(PMTask, pk=pk, is_deleted=False)

    if task.status == 'COMPLETED':
        messages.error(request, 'This task is already completed.')
        return redirect('maintenance:pm_task_detail', pk=pk)

    if request.method == 'POST':
        form = PMTaskCompleteForm(request.POST)
        if form.is_valid():
            task.actual_start = form.cleaned_data['actual_start']
            task.actual_end = form.cleaned_data['actual_end']
            task.notes = form.cleaned_data.get('notes', '')
            task.findings = form.cleaned_data.get('findings', '')
            task.performed_by = request.user
            task.status = 'COMPLETED'

            # Calculate duration
            delta = task.actual_end - task.actual_start
            task.duration_minutes = int(delta.total_seconds() / 60)

            task.save()

            # Update schedule
            task.complete(
                performed_by=request.user,
                notes=task.notes,
                findings=task.findings,
                meter_reading=form.cleaned_data.get('meter_reading')
            )

            messages.success(request, 'PM task completed successfully.')

            # Create follow-up work order if needed
            if form.cleaned_data.get('create_work_order') and task.findings:
                wo = WorkOrder.objects.create(
                    asset=task.schedule.asset,
                    title=f'Follow-up from PM: {task.schedule.pm_template.name}',
                    description=f'Issues found during PM:\n{task.findings}',
                    work_order_type='CORRECTIVE',
                    priority='MEDIUM',
                    status='PLANNED',
                    source_pm_task=task,
                    created_by=request.user,
                )
                messages.info(request, f'Follow-up work order {wo.work_order_number} created.')

            return redirect('maintenance:pm_task_detail', pk=pk)
    else:
        form = PMTaskCompleteForm()

    return render(request, 'maintenance/pm_task_complete.html', {'form': form, 'task': task})


# ==================== DOWNTIME VIEWS ====================

@login_required
def downtime_list(request):
    """List downtime events."""
    form = DateRangeForm(request.GET)
    events = DowntimeEvent.objects.all().select_related('asset', 'work_order').order_by('-start_time')

    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        if start_date:
            events = events.filter(start_time__date__gte=start_date)
        if end_date:
            events = events.filter(end_time__date__lte=end_date)

    paginator = Paginator(events, 20)
    page = request.GET.get('page')
    events_page = paginator.get_page(page)

    context = {
        'events': events_page,
        'form': form,
    }
    return render(request, 'maintenance/downtime_list.html', context)


@login_required
def downtime_detail(request, pk):
    """View downtime event details."""
    event = get_object_or_404(DowntimeEvent, pk=pk)
    impacts = event.production_impacts.all()

    context = {
        'event': event,
        'impacts': impacts,
    }
    return render(request, 'maintenance/downtime_detail.html', context)


@login_required
@permission_required('maintenance.can_record_downtime', raise_exception=True)
def downtime_create(request):
    """Record new downtime event."""
    if request.method == 'POST':
        form = DowntimeEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.reported_by = request.user
            event.created_by = request.user
            event.save()
            messages.success(request, 'Downtime event recorded successfully.')
            return redirect('maintenance:downtime_detail', pk=event.pk)
    else:
        form = DowntimeEventForm()

    return render(request, 'maintenance/downtime_form.html', {'form': form})


@login_required
def downtime_impact(request):
    """Production impact report."""
    form = DateRangeForm(request.GET)

    start_date = None
    end_date = None
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

    summary = DowntimeService.get_production_impact_summary(start_date, end_date)
    top_assets = DowntimeService.get_top_downtime_assets(limit=10)
    by_reason = DowntimeService.get_downtime_by_reason(start_date, end_date)

    context = {
        'form': form,
        'summary': summary,
        'top_assets': top_assets,
        'by_reason': by_reason,
    }
    return render(request, 'maintenance/downtime_impact.html', context)


@login_required
def production_impact_create(request, downtime_pk):
    """Add production impact to downtime event."""
    downtime_event = get_object_or_404(DowntimeEvent, pk=downtime_pk)

    if request.method == 'POST':
        form = ProductionImpactForm(request.POST)
        if form.is_valid():
            impact = form.save(commit=False)
            impact.downtime_event = downtime_event
            impact.created_by = request.user
            impact.save()

            # Update downtime event flag
            downtime_event.has_production_impact = True
            downtime_event.save()

            messages.success(request, 'Production impact recorded.')
            return redirect('maintenance:downtime_detail', pk=downtime_pk)
    else:
        form = ProductionImpactForm(initial={'downtime_event': downtime_event})

    return render(request, 'maintenance/production_impact_form.html', {
        'form': form,
        'downtime_event': downtime_event
    })


# ==================== REPORTS ====================

@login_required
def reports_dashboard(request):
    """Reports and analytics dashboard."""
    # Get summary stats
    downtime_summary = DowntimeService.get_downtime_summary()
    impact_summary = DowntimeService.get_production_impact_summary()
    warranty_expiring = AssetService.get_warranty_expiring_assets(days=30)

    context = {
        'downtime_summary': downtime_summary,
        'impact_summary': impact_summary,
        'warranty_expiring': warranty_expiring,
    }
    return render(request, 'maintenance/reports_dashboard.html', context)


# ==================== API ENDPOINTS ====================

@login_required
def api_asset_search(request):
    """API endpoint for asset autocomplete."""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})

    assets = Asset.objects.filter(
        is_deleted=False
    ).filter(
        Q(asset_code__icontains=query) |
        Q(name__icontains=query) |
        Q(serial_number__icontains=query)
    )[:10]

    results = [
        {
            'id': asset.pk,
            'code': asset.asset_code,
            'name': asset.name,
            'text': f'{asset.asset_code} - {asset.name}'
        }
        for asset in assets
    ]

    return JsonResponse({'results': results})


@login_required
def api_dashboard_stats(request):
    """API endpoint for dashboard statistics."""
    stats = MaintenanceService.get_dashboard_stats()
    return JsonResponse(stats)
