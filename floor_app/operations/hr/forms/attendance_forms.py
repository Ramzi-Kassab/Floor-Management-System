"""
Attendance Management Forms
Forms for attendance tracking, overtime approval, and delay management
Supports both punch machine and manual entry systems
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, timedelta
from decimal import Decimal

from floor_app.operations.hr.models import HREmployee
from floor_app.operations.hr.models.attendance import (
    AttendanceRecord, AttendanceStatus,
    OvertimeRequest, OvertimeStatus, OvertimeType
)
from floor_app.operations.hr.models.configuration import (
    OvertimeConfiguration, AttendanceConfiguration,
    DelayIncident, DelayReason
)


class AttendanceEntryForm(forms.ModelForm):
    """
    Form for manual attendance entry (for employees without punch machines)
    """
    class Meta:
        model = AttendanceRecord
        fields = [
            'employee', 'date', 'actual_start', 'actual_end',
            'employee_notes', 'location_name', 'is_remote_work'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'actual_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'employee_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Office, Site, Remote, etc.'}),
            'is_remote_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # All employees can have manual entry based on configuration
        self.fields['employee'].queryset = HREmployee.objects.filter(
            is_deleted=False
        ).select_related('user').order_by('employee_no')

        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()

        # Add help text from configuration
        config = AttendanceConfiguration.get_active_config()
        if config.require_supervisor_approval_manual_entry:
            self.fields['employee_notes'].help_text = 'Note: Manual entries require supervisor approval'

    def clean(self):
        """Validate attendance entry"""
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        date = cleaned_data.get('date')
        check_in = cleaned_data.get('actual_start')
        check_out = cleaned_data.get('actual_end')

        if not all([employee, date, check_in]):
            return cleaned_data

        # Check if manual entry is allowed
        config = AttendanceConfiguration.get_active_config()
        if not config.allow_manual_entry:
            raise ValidationError('Manual attendance entry is not allowed by current policy.')

        # Validate date is not in future
        if date > timezone.now().date():
            raise ValidationError('Cannot record attendance for future dates.')

        # Validate check-in and check-out times
        if check_out and check_in >= check_out:
            raise ValidationError('Check-out time must be after check-in time.')

        # Check for duplicate entry
        existing = AttendanceRecord.objects.filter(
            employee=employee,
            date=date,
            is_deleted=False
        )
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise ValidationError(
                f'Attendance already recorded for {employee.get_full_name()} on {date}.'
            )

        return cleaned_data


class PunchMachineImportForm(forms.Form):
    """
    Form for importing punch machine data (CSV/Excel)
    """
    file = forms.FileField(
        label='Punch Machine Data File',
        help_text='Upload CSV or Excel file from punch machine system',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx,.xls'})
    )
    date_from = forms.DateField(
        label='From Date',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        label='To Date',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    override_existing = forms.BooleanField(
        label='Override existing records',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Replace existing attendance records with imported data'
    )

    def clean(self):
        """Validate import parameters"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError('From date must be before or equal to to date.')

        return cleaned_data


class OvertimeRequestForm(forms.ModelForm):
    """
    Form for requesting overtime work approval
    Uses configurable overtime limits and rates
    """
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        label='Start Time'
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        label='End Time'
    )

    class Meta:
        model = OvertimeRequest
        fields = [
            'employee', 'date', 'overtime_type', 'reason',
            'work_description'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'overtime_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'work_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Get current configuration
        config = OvertimeConfiguration.get_active_config()

        # If creating new request, set employee to current user
        if not self.instance.pk and self.user:
            try:
                employee = HREmployee.objects.get(user=self.user, is_deleted=False)
                self.fields['employee'].initial = employee
                self.fields['employee'].widget = forms.HiddenInput()
            except HREmployee.DoesNotExist:
                pass

        # Add dynamic help text based on configuration
        self.fields['overtime_type'].help_text = (
            f'Regular OT: {config.regular_overtime_rate}x pay | '
            f'Weekend: {config.weekend_overtime_rate}x pay | '
            f'Holiday: {config.holiday_overtime_rate}x pay'
        )
        self.fields['date'].help_text = (
            f'Max {config.max_days_advance_request} days in advance. '
            f'{"Requires manager approval." if config.requires_manager_approval else ""}'
        )

        # Show overtime limits in form help
        limits_help = (
            f'Limits: {config.max_overtime_hours_per_day}h/day, '
            f'{config.max_overtime_hours_per_week}h/week, '
            f'{config.max_overtime_hours_per_quarter}h/quarter'
        )
        self.fields['reason'].help_text = limits_help

    def clean(self):
        """Validate overtime request according to configurable limits"""
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        overtime_type = cleaned_data.get('overtime_type')

        if not all([employee, date, start_time, end_time]):
            return cleaned_data

        # Get configuration
        config = OvertimeConfiguration.get_active_config()

        # Calculate overtime hours
        start_datetime = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)

        if end_time < start_time:
            # Overtime extends past midnight
            end_datetime += timedelta(days=1)

        overtime_hours = (end_datetime - start_datetime).total_seconds() / 3600
        cleaned_data['planned_hours'] = Decimal(str(round(overtime_hours, 2)))

        # Validate against daily limit
        if overtime_hours > float(config.max_overtime_hours_per_day):
            raise ValidationError(
                f'Overtime policy limits overtime to maximum {config.max_overtime_hours_per_day} hours per day. '
                f'Requested: {overtime_hours:.1f} hours.'
            )

        # Check weekly overtime limit
        week_start = date - timedelta(days=7)
        total_week_overtime = OvertimeRequest.objects.filter(
            employee=employee,
            date__gte=week_start,
            date__lt=date,
            status=OvertimeStatus.APPROVED,
            is_deleted=False
        ).aggregate(
            total=models.Sum('planned_hours')
        )['total'] or Decimal('0')

        if total_week_overtime + Decimal(str(overtime_hours)) > config.max_overtime_hours_per_week:
            raise ValidationError(
                f'Overtime policy limits overtime to {config.max_overtime_hours_per_week} hours per week. '
                f'Current week total: {total_week_overtime} hours. '
                f'Requested: {overtime_hours} hours.'
            )

        # Check quarterly overtime limit
        quarter_start = date - timedelta(days=90)
        total_approved_overtime = OvertimeRequest.objects.filter(
            employee=employee,
            date__gte=quarter_start,
            date__lte=date,
            status=OvertimeStatus.APPROVED,
            is_deleted=False
        ).aggregate(
            total=models.Sum('planned_hours')
        )['total'] or Decimal('0')

        if total_approved_overtime + Decimal(str(overtime_hours)) > config.max_overtime_hours_per_quarter:
            raise ValidationError(
                f'Overtime policy limits overtime to {config.max_overtime_hours_per_quarter} hours per quarter. '
                f'Current quarter total: {total_approved_overtime} hours. '
                f'Requested: {overtime_hours} hours.'
            )

        # Validate future request
        max_advance_days = config.max_days_advance_request
        if date > timezone.now().date() + timedelta(days=max_advance_days):
            raise ValidationError(
                f'Overtime requests cannot be made more than {max_advance_days} days in advance.'
            )

        # Validate retroactive requests
        if date < timezone.now().date() and not config.allow_retroactive_requests:
            raise ValidationError('Retroactive overtime requests are not allowed by current policy.')

        # Set rate multiplier based on overtime type
        cleaned_data['rate_multiplier'] = config.get_rate_for_overtime_type(overtime_type)

        # Weekend work compensation
        if overtime_type == OvertimeType.WEEKEND and config.weekend_work_requires_compensatory_day:
            cleaned_data['is_compensatory_off'] = True

        return cleaned_data


class OvertimeApprovalForm(forms.Form):
    """
    Form for managers to approve/reject overtime requests
    """
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Decision'
    )
    approval_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Manager Notes',
        help_text='Optional notes (required for rejection)'
    )
    approved_hours = forms.DecimalField(
        required=False,
        max_digits=4,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        label='Approved Hours',
        help_text='If different from requested hours'
    )

    def __init__(self, *args, overtime_request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.overtime_request = overtime_request

        # Get configuration for limits
        config = OvertimeConfiguration.get_active_config()

        if overtime_request:
            self.fields['approved_hours'].initial = overtime_request.planned_hours
            self.fields['approved_hours'].help_text = (
                f'Max {config.max_overtime_hours_per_day} hours/day per policy'
            )

    def clean(self):
        """Validate approval decision"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        notes = cleaned_data.get('approval_notes')
        approved_hours = cleaned_data.get('approved_hours')

        # Get configuration
        config = OvertimeConfiguration.get_active_config()

        # Require notes for rejection
        if action == 'reject' and not notes:
            raise ValidationError('Please provide a reason for rejection.')

        # Validate approved hours if approving
        if action == 'approve':
            if not approved_hours or approved_hours <= 0:
                raise ValidationError('Please specify approved overtime hours.')

            # Check against policy limit
            max_daily = float(config.max_overtime_hours_per_day)
            if approved_hours > max_daily:
                raise ValidationError(
                    f'Cannot approve more than {max_daily} hours overtime per day (company policy).'
                )

        return cleaned_data


class DelayIncidentForm(forms.ModelForm):
    """
    Form for recording employee delays/late arrivals
    """
    class Meta:
        model = DelayIncident
        fields = [
            'employee', 'date', 'scheduled_time', 'actual_time',
            'delay_reason', 'employee_explanation', 'has_valid_excuse',
            'supporting_document'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scheduled_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'actual_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'delay_reason': forms.Select(attrs={'class': 'form-select'}),
            'employee_explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'has_valid_excuse': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'supporting_document': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # If employee is submitting, set to current user
        if not self.instance.pk and self.user:
            try:
                employee = HREmployee.objects.get(user=self.user, is_deleted=False)
                self.fields['employee'].initial = employee
                self.fields['employee'].widget = forms.HiddenInput()
            except HREmployee.DoesNotExist:
                pass

    def clean(self):
        """Validate delay incident"""
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        scheduled = cleaned_data.get('scheduled_time')
        actual = cleaned_data.get('actual_time')
        employee = cleaned_data.get('employee')

        if not all([date, scheduled, actual]):
            return cleaned_data

        # Validate actual is after scheduled
        if actual <= scheduled:
            raise ValidationError('Actual arrival time must be after scheduled time.')

        # Calculate delay duration
        scheduled_datetime = datetime.combine(date, scheduled)
        actual_datetime = datetime.combine(date, actual)
        delay_minutes = int((actual_datetime - scheduled_datetime).total_seconds() / 60)

        cleaned_data['delay_minutes'] = delay_minutes

        # Check for duplicate
        existing = DelayIncident.objects.filter(
            employee=employee,
            date=date
        )
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise ValidationError('Delay already recorded for this date.')

        return cleaned_data


class AttendanceSearchForm(forms.Form):
    """
    Form for searching and filtering attendance records
    """
    employee = forms.ModelChoiceField(
        queryset=HREmployee.objects.filter(is_deleted=False),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Employee',
        empty_label='All Employees'
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='From Date'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='To Date'
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + AttendanceStatus.CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Status'
    )
    has_punch_machine = forms.ChoiceField(
        choices=[('', 'All'), ('yes', 'Punch Machine'), ('no', 'Manual Entry')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Entry Type'
    )
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Department',
        empty_label='All Departments'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from floor_app.operations.hr.models import Department
        self.fields['department'].queryset = Department.objects.filter(
            is_deleted=False
        ).order_by('name')

        # Set default date range to current month
        if not self.data:
            today = timezone.now().date()
            self.fields['date_from'].initial = today.replace(day=1)
            self.fields['date_to'].initial = today

    def clean(self):
        """Validate search parameters"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError('From date must be before or equal to to date.')

        return cleaned_data
