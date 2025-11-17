"""
Quality Management - Views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta

from .models import (
    NonconformanceReport,
    NCRRootCauseAnalysis,
    NCRCorrectiveAction,
    CalibratedEquipment,
    CalibrationRecord,
    QualityDisposition,
    DefectCategory,
    RootCauseCategory,
    AcceptanceCriteriaTemplate,
)
from .forms import (
    NCRForm,
    NCRRootCauseAnalysisForm,
    NCRCorrectiveActionForm,
    CalibratedEquipmentForm,
    CalibrationRecordForm,
    QualityDispositionForm,
)


@login_required
def dashboard(request):
    """Quality Management Dashboard."""
    # NCR Stats
    open_ncrs = NonconformanceReport.objects.exclude(status='CLOSED').exclude(status='CANCELLED')
    ncr_stats = {
        'total_open': open_ncrs.count(),
        'critical': open_ncrs.filter(severity='CRITICAL').count(),
        'major': open_ncrs.filter(severity='MAJOR').count(),
        'overdue': sum(1 for ncr in open_ncrs if ncr.is_overdue),
    }

    # Recent NCRs
    recent_ncrs = NonconformanceReport.objects.order_by('-reported_at')[:10]

    # Calibration Stats
    today = timezone.now().date()
    thirty_days = today + timedelta(days=30)

    calibration_stats = {
        'total_equipment': CalibratedEquipment.objects.count(),
        'overdue': CalibratedEquipment.objects.filter(status='OVERDUE').count(),
        'due_soon': CalibratedEquipment.objects.filter(status='DUE_SOON').count(),
        'in_service': CalibratedEquipment.objects.filter(status='IN_SERVICE').count(),
    }

    # Equipment due soon
    equipment_due = CalibratedEquipment.objects.filter(
        next_calibration_due__lte=thirty_days,
        next_calibration_due__gte=today
    ).order_by('next_calibration_due')[:10]

    # Disposition Stats
    disposition_stats = {
        'pending_release': QualityDisposition.objects.filter(
            released_for_shipment=False,
            decision='APPROVED'
        ).count(),
        'on_hold': QualityDisposition.objects.filter(decision='HOLD').count(),
        'released_today': QualityDisposition.objects.filter(
            release_date__date=today
        ).count(),
    }

    # NCR by Category Chart Data
    ncr_by_category = DefectCategory.objects.annotate(
        ncr_count=Count('ncrs', filter=Q(ncrs__is_deleted=False))
    ).filter(ncr_count__gt=0).order_by('-ncr_count')[:5]

    context = {
        'ncr_stats': ncr_stats,
        'recent_ncrs': recent_ncrs,
        'calibration_stats': calibration_stats,
        'equipment_due': equipment_due,
        'disposition_stats': disposition_stats,
        'ncr_by_category': ncr_by_category,
    }
    return render(request, 'quality/dashboard.html', context)


# === NCR Management ===

@login_required
def ncr_list(request):
    """List all NCRs with filtering."""
    ncrs = NonconformanceReport.objects.select_related('defect_category', 'reported_by').all()

    # Filtering
    status = request.GET.get('status')
    severity = request.GET.get('severity')
    ncr_type = request.GET.get('type')

    if status:
        ncrs = ncrs.filter(status=status)
    if severity:
        ncrs = ncrs.filter(severity=severity)
    if ncr_type:
        ncrs = ncrs.filter(ncr_type=ncr_type)

    paginator = Paginator(ncrs, 20)
    page = request.GET.get('page')
    ncrs = paginator.get_page(page)

    context = {
        'ncrs': ncrs,
        'status_choices': NonconformanceReport.NCR_STATUS_CHOICES,
        'severity_choices': NonconformanceReport.SEVERITY_CHOICES,
        'type_choices': NonconformanceReport.NCR_TYPE_CHOICES,
    }
    return render(request, 'quality/ncr/list.html', context)


@login_required
def ncr_create(request):
    """Create a new NCR."""
    if request.method == 'POST':
        form = NCRForm(request.POST)
        if form.is_valid():
            ncr = form.save(commit=False)
            ncr.ncr_number = NonconformanceReport.generate_ncr_number()
            ncr.reported_by = request.user
            ncr.save()
            messages.success(request, f'NCR {ncr.ncr_number} created successfully.')
            return redirect('quality:ncr_detail', pk=ncr.pk)
    else:
        form = NCRForm()

    context = {'form': form, 'title': 'Create NCR'}
    return render(request, 'quality/ncr/form.html', context)


@login_required
def ncr_detail(request, pk):
    """View NCR details."""
    ncr = get_object_or_404(NonconformanceReport, pk=pk)
    analyses = ncr.root_cause_analyses.all()
    actions = ncr.corrective_actions.all()

    context = {
        'ncr': ncr,
        'analyses': analyses,
        'actions': actions,
    }
    return render(request, 'quality/ncr/detail.html', context)


@login_required
def ncr_edit(request, pk):
    """Edit an NCR."""
    ncr = get_object_or_404(NonconformanceReport, pk=pk)

    if request.method == 'POST':
        form = NCRForm(request.POST, instance=ncr)
        if form.is_valid():
            form.save()
            messages.success(request, f'NCR {ncr.ncr_number} updated successfully.')
            return redirect('quality:ncr_detail', pk=ncr.pk)
    else:
        form = NCRForm(instance=ncr)

    context = {'form': form, 'ncr': ncr, 'title': f'Edit NCR {ncr.ncr_number}'}
    return render(request, 'quality/ncr/form.html', context)


@login_required
def ncr_add_analysis(request, pk):
    """Add root cause analysis to NCR."""
    ncr = get_object_or_404(NonconformanceReport, pk=pk)

    if request.method == 'POST':
        form = NCRRootCauseAnalysisForm(request.POST)
        if form.is_valid():
            analysis = form.save(commit=False)
            analysis.ncr = ncr
            analysis.analyzed_by = request.user
            analysis.save()
            ncr.status = 'ROOT_CAUSE'
            ncr.save()
            messages.success(request, 'Root cause analysis added.')
            return redirect('quality:ncr_detail', pk=ncr.pk)
    else:
        form = NCRRootCauseAnalysisForm()

    context = {'form': form, 'ncr': ncr}
    return render(request, 'quality/ncr/add_analysis.html', context)


@login_required
def ncr_add_action(request, pk):
    """Add corrective action to NCR."""
    ncr = get_object_or_404(NonconformanceReport, pk=pk)

    if request.method == 'POST':
        form = NCRCorrectiveActionForm(request.POST)
        if form.is_valid():
            action = form.save(commit=False)
            action.ncr = ncr
            action.save()
            if ncr.status == 'ROOT_CAUSE':
                ncr.status = 'CORRECTIVE'
                ncr.save()
            messages.success(request, 'Corrective action added.')
            return redirect('quality:ncr_detail', pk=ncr.pk)
    else:
        form = NCRCorrectiveActionForm()

    context = {'form': form, 'ncr': ncr}
    return render(request, 'quality/ncr/add_action.html', context)


@login_required
def ncr_close(request, pk):
    """Close an NCR."""
    ncr = get_object_or_404(NonconformanceReport, pk=pk)

    if request.method == 'POST':
        ncr.close(request.user)
        messages.success(request, f'NCR {ncr.ncr_number} has been closed.')
        return redirect('quality:ncr_detail', pk=ncr.pk)

    context = {'ncr': ncr}
    return render(request, 'quality/ncr/close_confirm.html', context)


# === Calibration Management ===

@login_required
def calibration_list(request):
    """Calibration overview."""
    equipment = CalibratedEquipment.objects.all()
    overdue = equipment.filter(status='OVERDUE')
    due_soon = equipment.filter(status='DUE_SOON')

    context = {
        'overdue': overdue,
        'due_soon': due_soon,
        'total_count': equipment.count(),
    }
    return render(request, 'quality/calibration/overview.html', context)


@login_required
def equipment_list(request):
    """List all calibrated equipment."""
    equipment = CalibratedEquipment.objects.all()

    # Filtering
    status = request.GET.get('status')
    equipment_type = request.GET.get('type')

    if status:
        equipment = equipment.filter(status=status)
    if equipment_type:
        equipment = equipment.filter(equipment_type=equipment_type)

    paginator = Paginator(equipment, 20)
    page = request.GET.get('page')
    equipment = paginator.get_page(page)

    context = {
        'equipment': equipment,
        'status_choices': CalibratedEquipment.STATUS_CHOICES,
        'type_choices': CalibratedEquipment.EQUIPMENT_TYPE_CHOICES,
    }
    return render(request, 'quality/calibration/equipment_list.html', context)


@login_required
def equipment_create(request):
    """Create new calibrated equipment."""
    if request.method == 'POST':
        form = CalibratedEquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save()
            messages.success(request, f'Equipment {equipment.equipment_id} added.')
            return redirect('quality:equipment_detail', pk=equipment.pk)
    else:
        form = CalibratedEquipmentForm()

    context = {'form': form, 'title': 'Add Equipment'}
    return render(request, 'quality/calibration/equipment_form.html', context)


@login_required
def equipment_detail(request, pk):
    """View equipment details and calibration history."""
    equipment = get_object_or_404(CalibratedEquipment, pk=pk)
    calibration_history = equipment.calibration_records.all()

    context = {
        'equipment': equipment,
        'calibration_history': calibration_history,
    }
    return render(request, 'quality/calibration/equipment_detail.html', context)


@login_required
def equipment_edit(request, pk):
    """Edit equipment."""
    equipment = get_object_or_404(CalibratedEquipment, pk=pk)

    if request.method == 'POST':
        form = CalibratedEquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Equipment {equipment.equipment_id} updated.')
            return redirect('quality:equipment_detail', pk=equipment.pk)
    else:
        form = CalibratedEquipmentForm(instance=equipment)

    context = {'form': form, 'equipment': equipment, 'title': f'Edit {equipment.equipment_id}'}
    return render(request, 'quality/calibration/equipment_form.html', context)


@login_required
def record_calibration(request, pk):
    """Record a calibration event."""
    equipment = get_object_or_404(CalibratedEquipment, pk=pk)

    if request.method == 'POST':
        form = CalibrationRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.equipment = equipment
            record.save()
            messages.success(request, 'Calibration recorded successfully.')
            return redirect('quality:equipment_detail', pk=equipment.pk)
    else:
        form = CalibrationRecordForm()

    context = {'form': form, 'equipment': equipment}
    return render(request, 'quality/calibration/record_form.html', context)


@login_required
def calibration_due(request):
    """List equipment due for calibration soon."""
    equipment = CalibratedEquipment.objects.filter(status='DUE_SOON').order_by('next_calibration_due')

    context = {'equipment': equipment, 'title': 'Calibration Due Soon'}
    return render(request, 'quality/calibration/due_list.html', context)


@login_required
def calibration_overdue(request):
    """List overdue calibrations."""
    equipment = CalibratedEquipment.objects.filter(status='OVERDUE').order_by('next_calibration_due')

    context = {'equipment': equipment, 'title': 'Overdue Calibrations'}
    return render(request, 'quality/calibration/due_list.html', context)


# === Quality Disposition ===

@login_required
def disposition_list(request):
    """List quality dispositions."""
    dispositions = QualityDisposition.objects.all()

    # Filtering
    decision = request.GET.get('decision')
    released = request.GET.get('released')

    if decision:
        dispositions = dispositions.filter(decision=decision)
    if released:
        dispositions = dispositions.filter(released_for_shipment=(released == 'true'))

    paginator = Paginator(dispositions, 20)
    page = request.GET.get('page')
    dispositions = paginator.get_page(page)

    context = {
        'dispositions': dispositions,
        'decision_choices': QualityDisposition.DECISION_CHOICES,
    }
    return render(request, 'quality/disposition/list.html', context)


@login_required
def disposition_create(request):
    """Create quality disposition."""
    if request.method == 'POST':
        form = QualityDispositionForm(request.POST)
        if form.is_valid():
            disposition = form.save(commit=False)
            disposition.quality_engineer = request.user
            disposition.save()
            form.save_m2m()
            messages.success(request, 'Quality disposition created.')
            return redirect('quality:disposition_detail', pk=disposition.pk)
    else:
        form = QualityDispositionForm()

    context = {'form': form, 'title': 'Create Disposition'}
    return render(request, 'quality/disposition/form.html', context)


@login_required
def disposition_detail(request, pk):
    """View disposition details."""
    disposition = get_object_or_404(QualityDisposition, pk=pk)

    context = {'disposition': disposition}
    return render(request, 'quality/disposition/detail.html', context)


@login_required
def disposition_release(request, pk):
    """Release disposition for shipment."""
    disposition = get_object_or_404(QualityDisposition, pk=pk)

    if request.method == 'POST':
        try:
            disposition.release(request.user)
            messages.success(request, 'Job released for shipment.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('quality:disposition_detail', pk=disposition.pk)

    context = {'disposition': disposition}
    return render(request, 'quality/disposition/release_confirm.html', context)


@login_required
def generate_coc(request, pk):
    """Generate Certificate of Conformance."""
    disposition = get_object_or_404(QualityDisposition, pk=pk)

    if request.method == 'POST':
        coc_number = disposition.generate_coc_number()
        messages.success(request, f'COC {coc_number} generated.')
        return redirect('quality:disposition_detail', pk=disposition.pk)

    context = {'disposition': disposition}
    return render(request, 'quality/disposition/generate_coc_confirm.html', context)


# === Acceptance Criteria ===

@login_required
def criteria_list(request):
    """List acceptance criteria templates."""
    templates = AcceptanceCriteriaTemplate.objects.filter(is_active=True)

    context = {'templates': templates}
    return render(request, 'quality/acceptance/list.html', context)


@login_required
def criteria_detail(request, pk):
    """View criteria template details."""
    template = get_object_or_404(AcceptanceCriteriaTemplate, pk=pk)

    context = {'template': template}
    return render(request, 'quality/acceptance/detail.html', context)


# === Reports ===

@login_required
def reports_dashboard(request):
    """Quality reports dashboard."""
    return render(request, 'quality/reports/dashboard.html')


@login_required
def ncr_summary_report(request):
    """NCR summary report."""
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    ncrs = NonconformanceReport.objects.filter(
        reported_at__date__gte=start_date,
        reported_at__date__lte=end_date
    )

    summary = {
        'total': ncrs.count(),
        'by_type': ncrs.values('ncr_type').annotate(count=Count('id')),
        'by_severity': ncrs.values('severity').annotate(count=Count('id')),
        'by_disposition': ncrs.values('disposition').annotate(count=Count('id')),
        'total_cost': ncrs.aggregate(Sum('actual_cost_impact'))['actual_cost_impact__sum'] or 0,
    }

    context = {
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'quality/reports/ncr_summary.html', context)


@login_required
def calibration_status_report(request):
    """Calibration status report."""
    equipment = CalibratedEquipment.objects.all()

    summary = {
        'total': equipment.count(),
        'by_status': equipment.values('status').annotate(count=Count('id')),
        'by_type': equipment.values('equipment_type').annotate(count=Count('id')),
        'critical_overdue': equipment.filter(is_critical=True, status='OVERDUE').count(),
    }

    context = {'summary': summary}
    return render(request, 'quality/reports/calibration_status.html', context)


# === Settings ===

@login_required
def settings_dashboard(request):
    """Quality settings dashboard."""
    defect_categories = DefectCategory.objects.all()
    root_cause_categories = RootCauseCategory.objects.all()

    context = {
        'defect_categories': defect_categories,
        'root_cause_categories': root_cause_categories,
    }
    return render(request, 'quality/settings/dashboard.html', context)
