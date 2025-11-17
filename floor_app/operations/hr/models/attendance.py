"""
Attendance Management Models

Tracks employee attendance, overtime, and time management.
"""

from django.db import models
from django.utils import timezone
from floor_app.mixins import AuditMixin


class AttendanceStatus:
    """Attendance status types"""
    PRESENT = 'PRESENT'
    ABSENT = 'ABSENT'
    LATE = 'LATE'
    EARLY_LEAVE = 'EARLY_LEAVE'
    HALF_DAY = 'HALF_DAY'
    ON_LEAVE = 'ON_LEAVE'
    HOLIDAY = 'HOLIDAY'
    WEEKEND = 'WEEKEND'

    CHOICES = [
        (PRESENT, 'Present'),
        (ABSENT, 'Absent'),
        (LATE, 'Late Arrival'),
        (EARLY_LEAVE, 'Early Leave'),
        (HALF_DAY, 'Half Day'),
        (ON_LEAVE, 'On Leave'),
        (HOLIDAY, 'Holiday'),
        (WEEKEND, 'Weekend'),
    ]


class OvertimeType:
    """Types of overtime"""
    REGULAR = 'REGULAR'
    WEEKEND = 'WEEKEND'
    HOLIDAY = 'HOLIDAY'
    NIGHT = 'NIGHT'

    CHOICES = [
        (REGULAR, 'Regular Overtime'),
        (WEEKEND, 'Weekend Overtime'),
        (HOLIDAY, 'Holiday Overtime'),
        (NIGHT, 'Night Shift Overtime'),
    ]


class OvertimeStatus:
    """Overtime request status"""
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'

    CHOICES = [
        (PENDING, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]


class AttendanceRecord(AuditMixin):
    """
    Daily attendance record for employees.
    """
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=15,
        choices=AttendanceStatus.CHOICES,
        default=AttendanceStatus.ABSENT,
        db_index=True
    )

    # Time Records
    scheduled_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Scheduled start time"
    )
    scheduled_end = models.TimeField(
        null=True,
        blank=True,
        help_text="Scheduled end time"
    )
    actual_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Actual check-in time"
    )
    actual_end = models.TimeField(
        null=True,
        blank=True,
        help_text="Actual check-out time"
    )

    # Break Time
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    total_break_minutes = models.IntegerField(default=0)

    # Work Hours
    scheduled_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=8,
        help_text="Scheduled work hours"
    )
    actual_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        help_text="Actual hours worked"
    )
    overtime_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        help_text="Overtime hours worked"
    )

    # Late/Early
    late_minutes = models.IntegerField(
        default=0,
        help_text="Minutes late to work"
    )
    early_leave_minutes = models.IntegerField(
        default=0,
        help_text="Minutes left early"
    )

    # Location (for rig/field workers)
    location_name = models.CharField(max_length=200, blank=True)
    is_remote_work = models.BooleanField(default=False)

    # Notes
    supervisor_notes = models.TextField(blank=True)
    employee_notes = models.TextField(blank=True)

    # QR Code tracking
    check_in_qcode_id = models.BigIntegerField(null=True, blank=True)
    check_out_qcode_id = models.BigIntegerField(null=True, blank=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by_id = models.BigIntegerField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'hr_attendance_record'
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        unique_together = [['employee', 'date']]
        ordering = ['-date', 'employee']
        indexes = [
            models.Index(fields=['employee', 'date'], name='ix_attendance_emp_date'),
            models.Index(fields=['date', 'status'], name='ix_attendance_date_status'),
        ]

    def __str__(self):
        return f"{self.employee.employee_no} - {self.date} - {self.get_status_display()}"

    def calculate_hours(self):
        """Calculate actual working hours"""
        if self.actual_start and self.actual_end:
            from datetime import datetime, timedelta

            start = datetime.combine(self.date, self.actual_start)
            end = datetime.combine(self.date, self.actual_end)

            if end < start:
                # Night shift - end is next day
                end = end + timedelta(days=1)

            total_minutes = (end - start).seconds / 60
            total_minutes -= self.total_break_minutes
            self.actual_hours = total_minutes / 60

            # Calculate overtime
            if self.actual_hours > self.scheduled_hours:
                self.overtime_hours = self.actual_hours - self.scheduled_hours
            else:
                self.overtime_hours = 0

            self.save(update_fields=['actual_hours', 'overtime_hours'])

    def calculate_late_minutes(self):
        """Calculate late arrival minutes"""
        if self.scheduled_start and self.actual_start:
            from datetime import datetime

            scheduled = datetime.combine(self.date, self.scheduled_start)
            actual = datetime.combine(self.date, self.actual_start)

            if actual > scheduled:
                self.late_minutes = int((actual - scheduled).seconds / 60)
                if self.late_minutes > 0:
                    self.status = AttendanceStatus.LATE
            else:
                self.late_minutes = 0

            self.save(update_fields=['late_minutes', 'status'])


class OvertimeRequest(AuditMixin):
    """
    Overtime request and approval tracking.
    """
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.CASCADE,
        related_name='overtime_requests'
    )

    request_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True
    )
    status = models.CharField(
        max_length=10,
        choices=OvertimeStatus.CHOICES,
        default=OvertimeStatus.PENDING,
        db_index=True
    )
    overtime_type = models.CharField(
        max_length=10,
        choices=OvertimeType.CHOICES,
        default=OvertimeType.REGULAR
    )

    # Date and Hours
    date = models.DateField()
    planned_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Planned overtime hours"
    )
    actual_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        help_text="Actual overtime hours worked"
    )

    # Reason
    reason = models.TextField()
    work_description = models.TextField(
        blank=True,
        help_text="Description of work done during overtime"
    )

    # Approval
    approver_id = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    rejected_by_id = models.BigIntegerField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Compensation
    rate_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.5,
        help_text="Overtime rate multiplier (1.5x, 2x, etc.)"
    )
    is_compensatory_off = models.BooleanField(
        default=False,
        help_text="Convert to compensatory off instead of payment"
    )

    class Meta:
        db_table = 'hr_overtime_request'
        verbose_name = 'Overtime Request'
        verbose_name_plural = 'Overtime Requests'
        ordering = ['-date']

    def __str__(self):
        return f"{self.request_number} - {self.employee.employee_no}"

    def approve(self, approver_id, notes=''):
        """Approve overtime request"""
        if self.status == OvertimeStatus.PENDING:
            self.status = OvertimeStatus.APPROVED
            self.approver_id = approver_id
            self.approved_at = timezone.now()
            self.approval_notes = notes
            self.save(update_fields=[
                'status', 'approver_id', 'approved_at', 'approval_notes'
            ])
            return True
        return False

    @classmethod
    def generate_request_number(cls):
        """Generate next request number"""
        year = timezone.now().year
        prefix = f'OT-{year}-'
        last_req = cls.objects.filter(
            request_number__startswith=prefix
        ).order_by('-request_number').first()

        if last_req:
            last_num = int(last_req.request_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class AttendanceSummary(AuditMixin):
    """
    Monthly attendance summary for reporting.
    """
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    year = models.IntegerField(db_index=True)
    month = models.IntegerField(db_index=True)

    # Days Count
    total_working_days = models.IntegerField(default=0)
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    days_late = models.IntegerField(default=0)
    days_early_leave = models.IntegerField(default=0)
    days_on_leave = models.IntegerField(default=0)
    days_half_day = models.DecimalField(max_digits=4, decimal_places=1, default=0)

    # Hours
    total_scheduled_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    total_actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    total_overtime_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    total_late_minutes = models.IntegerField(default=0)
    total_early_leave_minutes = models.IntegerField(default=0)

    # Percentages
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    punctuality_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    last_calculated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'hr_attendance_summary'
        verbose_name = 'Attendance Summary'
        verbose_name_plural = 'Attendance Summaries'
        unique_together = [['employee', 'year', 'month']]
        ordering = ['-year', '-month', 'employee']

    def __str__(self):
        return f"{self.employee.employee_no} - {self.year}/{self.month}"

    def calculate(self):
        """Calculate summary from attendance records"""
        records = AttendanceRecord.objects.filter(
            employee=self.employee,
            date__year=self.year,
            date__month=self.month
        )

        self.days_present = records.filter(
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]
        ).count()
        self.days_absent = records.filter(status=AttendanceStatus.ABSENT).count()
        self.days_late = records.filter(status=AttendanceStatus.LATE).count()
        self.days_on_leave = records.filter(status=AttendanceStatus.ON_LEAVE).count()

        self.total_actual_hours = records.aggregate(
            total=models.Sum('actual_hours')
        )['total'] or 0
        self.total_overtime_hours = records.aggregate(
            total=models.Sum('overtime_hours')
        )['total'] or 0
        self.total_late_minutes = records.aggregate(
            total=models.Sum('late_minutes')
        )['total'] or 0

        if self.total_working_days > 0:
            self.attendance_percentage = (self.days_present / self.total_working_days) * 100
            on_time_days = self.days_present - self.days_late
            self.punctuality_percentage = (on_time_days / self.total_working_days) * 100

        self.last_calculated_at = timezone.now()
        self.save()
