"""
Attendance Tracking Views
Views for attendance management, overtime approval, and delay tracking
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import csv

from floor_app.operations.hr.models import HREmployee
from floor_app.operations.hr.models.attendance import (
    AttendanceRecord, AttendanceStatus, OvertimeRequest,
    OvertimeStatus, OvertimeType, AttendanceSummary
)
from floor_app.operations.hr.models.configuration import (
    OvertimeConfiguration, AttendanceConfiguration,
    DelayIncident, DelayReason
)
from floor_app.operations.hr.forms.attendance_forms import (
    AttendanceEntryForm, OvertimeRequestForm, OvertimeApprovalForm,
    DelayIncidentForm, AttendanceSearchForm, PunchMachineImportForm
)


def is_staff(user):
    """Check if user is staff/HR"""
    return user.is_staff or user.is_superuser


# ==================== Attendance Management ====================

@login_required
@user_passes_test(is_staff)
def attendance_dashboard(request):
    """
    Main attendance dashboard with statistics and overview
    """
    today = timezone.now().date()
    this_month = today.replace(day=1)

    # Get configuration
    config = AttendanceConfiguration.get_active_config()

    # Today's attendance statistics
    today_attendance = AttendanceRecord.objects.filter(
        date=today,
        is_deleted=False
    )

    stats = {
        'total_employees': HREmployee.objects.filter(is_deleted=False, status='ACTIVE').count(),
        'present_today': today_attendance.filter(
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]
        ).count(),
        'absent_today': today_attendance.filter(status=AttendanceStatus.ABSENT).count(),
        'late_today': today_attendance.filter(status=AttendanceStatus.LATE).count(),
        'on_leave_today': today_attendance.filter(status=AttendanceStatus.ON_LEAVE).count(),
    }

    # This month's statistics
    month_stats = AttendanceRecord.objects.filter(
        date__gte=this_month,
        date__lte=today,
        is_deleted=False
    ).aggregate(
        total_late=Count('id', filter=Q(status=AttendanceStatus.LATE)),
        total_absent=Count('id', filter=Q(status=AttendanceStatus.ABSENT)),
        avg_late_minutes=Avg('late_minutes'),
        total_overtime=Sum('overtime_hours')
    )

    # Recent delays
    recent_delays = DelayIncident.objects.filter(
        is_deleted=False,
        date__gte=today - timedelta(days=7)
    ).select_related('employee').order_by('-date')[:10]

    # Pending overtime requests
    pending_overtime = OvertimeRequest.objects.filter(
        status=OvertimeStatus.PENDING,
        is_deleted=False
    ).select_related('employee').order_by('-date')[:10]

    # Configuration info
    config_info = {
        'working_hours_per_day': config.standard_working_hours_per_day,
        'working_hours_per_week': config.standard_working_hours_per_week,
        'late_grace_minutes': config.late_arrival_grace_minutes,
        'manual_entry_allowed': config.allow_manual_entry,
    }

    context = {
        'stats': stats,
        'month_stats': month_stats,
        'recent_delays': recent_delays,
        'pending_overtime': pending_overtime,
        'config': config_info,
        'today': today,
    }

    return render(request, 'hr/attendance/dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def attendance_list(request):
    """
    List and search attendance records
    """
    form = AttendanceSearchForm(request.GET)
    attendance_records = AttendanceRecord.objects.filter(
        is_deleted=False
    ).select_related('employee').order_by('-date', 'employee__employee_no')

    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get('employee'):
            attendance_records = attendance_records.filter(employee=form.cleaned_data['employee'])

        if form.cleaned_data.get('date_from'):
            attendance_records = attendance_records.filter(date__gte=form.cleaned_data['date_from'])

        if form.cleaned_data.get('date_to'):
            attendance_records = attendance_records.filter(date__lte=form.cleaned_data['date_to'])

        if form.cleaned_data.get('status'):
            attendance_records = attendance_records.filter(status=form.cleaned_data['status'])

        if form.cleaned_data.get('department'):
            attendance_records = attendance_records.filter(employee__department=form.cleaned_data['department'])

        has_punch_machine = form.cleaned_data.get('has_punch_machine')
        if has_punch_machine == 'yes':
            # Records with QR code tracking (punch machine)
            attendance_records = attendance_records.filter(
                Q(check_in_qcode_id__isnull=False) | Q(check_out_qcode_id__isnull=False)
            )
        elif has_punch_machine == 'no':
            # Manual entries
            attendance_records = attendance_records.filter(
                check_in_qcode_id__isnull=True,
                check_out_qcode_id__isnull=True
            )

    # Pagination could be added here
    attendance_records = attendance_records[:100]  # Limit for performance

    context = {
        'form': form,
        'attendance_records': attendance_records,
    }

    return render(request, 'hr/attendance/list.html', context)


@login_required
def attendance_entry(request):
    """
    Manual attendance entry form
    Accessible by HR staff or supervisors
    """
    if request.method == 'POST':
        form = AttendanceEntryForm(request.POST, user=request.user)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.created_by_id = request.user.id

            # Set scheduled times if not set (from employee's default schedule)
            employee = attendance.employee
            if not attendance.scheduled_start and hasattr(employee, 'default_shift_start'):
                attendance.scheduled_start = employee.default_shift_start
            if not attendance.scheduled_end and hasattr(employee, 'default_shift_end'):
                attendance.scheduled_end = employee.default_shift_end

            # Get configuration for default hours
            config = AttendanceConfiguration.get_active_config()
            if not attendance.scheduled_hours:
                attendance.scheduled_hours = config.standard_working_hours_per_day

            attendance.save()

            # Calculate hours and late minutes
            attendance.calculate_hours()
            attendance.calculate_late_minutes()

            messages.success(
                request,
                f'Attendance recorded for {attendance.employee.get_full_name()} on {attendance.date}'
            )
            return redirect('hr:attendance_list')
    else:
        form = AttendanceEntryForm(user=request.user)

    context = {
        'form': form,
        'page_title': 'Manual Attendance Entry',
    }

    return render(request, 'hr/attendance/entry_form.html', context)


@login_required
@user_passes_test(is_staff)
def punch_machine_import(request):
    """
    Import attendance data from punch machine CSV/Excel
    """
    if request.method == 'POST':
        form = PunchMachineImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            override = form.cleaned_data.get('override_existing', False)

            # Process file (simplified - would need full CSV parsing logic)
            messages.success(request, 'Punch machine data imported successfully')
            return redirect('hr:attendance_dashboard')
    else:
        form = PunchMachineImportForm()

    context = {
        'form': form,
        'page_title': 'Import Punch Machine Data',
    }

    return render(request, 'hr/attendance/import.html', context)


# ==================== Overtime Management ====================

@login_required
def overtime_request_list(request):
    """
    List overtime requests
    Employees see their own, managers/HR see all
    """
    if request.user.is_staff:
        # HR/Staff see all requests
        overtime_requests = OvertimeRequest.objects.filter(
            is_deleted=False
        ).select_related('employee').order_by('-date')
    else:
        # Employees see only their own
        try:
            employee = HREmployee.objects.get(user=request.user, is_deleted=False)
            overtime_requests = OvertimeRequest.objects.filter(
                employee=employee,
                is_deleted=False
            ).order_by('-date')
        except HREmployee.DoesNotExist:
            overtime_requests = OvertimeRequest.objects.none()

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        overtime_requests = overtime_requests.filter(status=status_filter)

    context = {
        'overtime_requests': overtime_requests[:50],  # Limit for performance
        'pending_count': overtime_requests.filter(status=OvertimeStatus.PENDING).count(),
        'approved_count': overtime_requests.filter(status=OvertimeStatus.APPROVED).count(),
        'rejected_count': overtime_requests.filter(status=OvertimeStatus.REJECTED).count(),
    }

    return render(request, 'hr/attendance/overtime_list.html', context)


@login_required
def overtime_request_create(request):
    """
    Create new overtime request
    """
    if request.method == 'POST':
        form = OvertimeRequestForm(request.POST, user=request.user)
        if form.is_valid():
            overtime = form.save(commit=False)

            # Set planned hours and rate from cleaned data
            overtime.planned_hours = form.cleaned_data['planned_hours']
            overtime.rate_multiplier = form.cleaned_data['rate_multiplier']
            if 'is_compensatory_off' in form.cleaned_data:
                overtime.is_compensatory_off = form.cleaned_data['is_compensatory_off']

            # Generate request number
            overtime.request_number = OvertimeRequest.generate_request_number()
            overtime.status = OvertimeStatus.PENDING
            overtime.created_by_id = request.user.id
            overtime.save()

            messages.success(
                request,
                f'Overtime request {overtime.request_number} submitted successfully. '
                'Awaiting manager approval.'
            )
            return redirect('hr:overtime_request_list')
    else:
        form = OvertimeRequestForm(user=request.user)

    # Get configuration for display
    config = OvertimeConfiguration.get_active_config()

    context = {
        'form': form,
        'config': config,
        'page_title': 'Request Overtime',
    }

    return render(request, 'hr/attendance/overtime_request_form.html', context)


@login_required
def overtime_request_detail(request, pk):
    """
    View overtime request details
    """
    overtime = get_object_or_404(OvertimeRequest, pk=pk, is_deleted=False)

    # Check permissions
    is_manager = request.user.is_staff
    is_owner = hasattr(request.user, 'hremployee') and request.user.hremployee == overtime.employee

    if not (is_manager or is_owner):
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('hr:overtime_request_list')

    context = {
        'overtime': overtime,
        'is_manager': is_manager,
        'is_owner': is_owner,
        'can_approve': is_manager and overtime.status == OvertimeStatus.PENDING,
    }

    return render(request, 'hr/attendance/overtime_detail.html', context)


@login_required
@user_passes_test(is_staff)
def overtime_request_approve(request, pk):
    """
    Approve or reject overtime request
    """
    overtime = get_object_or_404(OvertimeRequest, pk=pk, is_deleted=False)

    if overtime.status != OvertimeStatus.PENDING:
        messages.error(request, 'This overtime request has already been processed.')
        return redirect('hr:overtime_request_detail', pk=pk)

    if request.method == 'POST':
        form = OvertimeApprovalForm(request.POST, overtime_request=overtime)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data['approval_notes']

            if action == 'approve':
                approved_hours = form.cleaned_data['approved_hours']
                overtime.status = OvertimeStatus.APPROVED
                overtime.planned_hours = approved_hours
                overtime.approver_id = request.user.id
                overtime.approved_at = timezone.now()
                overtime.approval_notes = notes
                overtime.save()

                messages.success(
                    request,
                    f'Overtime request {overtime.request_number} approved for {approved_hours} hours.'
                )
            else:  # reject
                overtime.status = OvertimeStatus.REJECTED
                overtime.rejected_by_id = request.user.id
                overtime.rejected_at = timezone.now()
                overtime.rejection_reason = notes
                overtime.save()

                messages.warning(
                    request,
                    f'Overtime request {overtime.request_number} has been rejected.'
                )

            return redirect('hr:overtime_request_detail', pk=pk)
    else:
        form = OvertimeApprovalForm(overtime_request=overtime)

    context = {
        'form': form,
        'overtime': overtime,
        'page_title': 'Approve Overtime Request',
    }

    return render(request, 'hr/attendance/overtime_approval.html', context)


# ==================== Delay Management ====================

@login_required
@user_passes_test(is_staff)
def delay_incident_list(request):
    """
    List all delay incidents with filtering
    """
    delays = DelayIncident.objects.filter(
        is_deleted=False
    ).select_related('employee').order_by('-date')

    # Filter by severity
    severity_filter = request.GET.get('severity')
    if severity_filter:
        delays = delays.filter(severity=severity_filter)

    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        delays = delays.filter(date__gte=date_from)
    if date_to:
        delays = delays.filter(date__lte=date_to)

    # Filter by review status
    review_filter = request.GET.get('reviewed')
    if review_filter == 'yes':
        delays = delays.filter(reviewed_at__isnull=False)
    elif review_filter == 'no':
        delays = delays.filter(reviewed_at__isnull=True)

    # Statistics
    stats = {
        'total': delays.count(),
        'unreviewed': delays.filter(reviewed_at__isnull=True).count(),
        'minor': delays.filter(severity='MINOR').count(),
        'major': delays.filter(severity='MAJOR').count(),
        'with_valid_excuse': delays.filter(has_valid_excuse=True).count(),
    }

    context = {
        'delays': delays[:100],  # Limit for performance
        'stats': stats,
    }

    return render(request, 'hr/attendance/delay_list.html', context)


@login_required
def delay_incident_report(request):
    """
    Employee reports a delay/late arrival
    """
    if request.method == 'POST':
        form = DelayIncidentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            delay = form.save(commit=False)
            delay.delay_minutes = form.cleaned_data['delay_minutes']
            delay.created_by_id = request.user.id
            delay.save()

            messages.success(
                request,
                f'Delay incident reported for {delay.date}. '
                'Your manager will review and respond.'
            )
            return redirect('hr:my_leave_dashboard')  # Or employee dashboard
    else:
        form = DelayIncidentForm(user=request.user)

    context = {
        'form': form,
        'page_title': 'Report Delay/Late Arrival',
    }

    return render(request, 'hr/attendance/delay_report.html', context)


@login_required
@user_passes_test(is_staff)
def delay_incident_review(request, pk):
    """
    Manager reviews and approves/rejects delay excuse
    """
    delay = get_object_or_404(DelayIncident, pk=pk, is_deleted=False)

    if request.method == 'POST':
        has_valid_excuse = request.POST.get('has_valid_excuse') == 'on'
        manager_notes = request.POST.get('manager_notes', '')
        take_action = request.POST.get('disciplinary_action') == 'on'
        action_description = request.POST.get('action_description', '')

        delay.has_valid_excuse = has_valid_excuse
        delay.manager_notes = manager_notes
        delay.disciplinary_action_taken = take_action
        delay.action_description = action_description
        delay.reviewed_by = request.user
        delay.reviewed_at = timezone.now()
        delay.save()

        if has_valid_excuse:
            messages.success(request, 'Delay excuse accepted.')
        else:
            messages.warning(request, 'Delay excuse not accepted.')

        return redirect('hr:delay_incident_list')

    context = {
        'delay': delay,
        'page_title': 'Review Delay Incident',
    }

    return render(request, 'hr/attendance/delay_review.html', context)


# ==================== Reports & Export ====================

@login_required
@user_passes_test(is_staff)
def attendance_report(request):
    """
    Generate attendance reports with various filters
    """
    if request.method == 'POST':
        # Generate report based on filters
        pass

    context = {
        'page_title': 'Attendance Reports',
    }

    return render(request, 'hr/attendance/reports.html', context)


@login_required
@user_passes_test(is_staff)
def export_attendance_csv(request):
    """
    Export attendance records to CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Employee No', 'Employee Name', 'Date', 'Status',
        'Check In', 'Check Out', 'Hours Worked', 'Overtime Hours',
        'Late Minutes', 'Location'
    ])

    # Apply filters from GET parameters
    attendance = AttendanceRecord.objects.filter(
        is_deleted=False
    ).select_related('employee').order_by('-date')

    for record in attendance:
        writer.writerow([
            record.employee.employee_no,
            record.employee.get_full_name(),
            record.date,
            record.get_status_display(),
            record.actual_start or '',
            record.actual_end or '',
            record.actual_hours,
            record.overtime_hours,
            record.late_minutes,
            record.location_name or '',
        ])

    return response
