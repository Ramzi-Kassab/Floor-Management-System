"""
HR Configuration Models
Configurable settings for attendance, overtime, and leave policies
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from floor_app.mixins import AuditMixin


class OvertimeConfiguration(AuditMixin):
    """
    Configurable overtime rules and pay rates
    Defaults set for Saudi Arabia labor law but can be customized
    """
    # Singleton pattern - only one active configuration
    is_active = models.BooleanField(
        default=True,
        help_text="Only one configuration can be active at a time"
    )

    configuration_name = models.CharField(
        max_length=100,
        default="Default Overtime Policy"
    )

    # Daily and Periodic Limits (KSA defaults: 3 hours/day, 90 hours/quarter)
    max_overtime_hours_per_day = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=3.00,
        validators=[MinValueValidator(0), MaxValueValidator(12)],
        help_text="Maximum overtime hours allowed per day (KSA default: 3)"
    )
    max_overtime_hours_per_week = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Maximum overtime hours allowed per week (KSA default: 15)"
    )
    max_overtime_hours_per_month = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30.00,
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        help_text="Maximum overtime hours allowed per month (KSA default: 30)"
    )
    max_overtime_hours_per_quarter = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=90.00,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Maximum overtime hours allowed per quarter (KSA default: 90)"
    )

    # Pay Rate Multipliers (KSA defaults)
    regular_overtime_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.50,
        validators=[MinValueValidator(1.00), MaxValueValidator(5.00)],
        help_text="Pay rate multiplier for regular overtime (KSA default: 1.5x = 150%)"
    )
    weekend_overtime_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.50,
        validators=[MinValueValidator(1.00), MaxValueValidator(5.00)],
        help_text="Pay rate multiplier for weekend overtime (KSA default: 1.5x + compensatory day)"
    )
    holiday_overtime_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=2.00,
        validators=[MinValueValidator(1.00), MaxValueValidator(5.00)],
        help_text="Pay rate multiplier for holiday overtime (KSA default: 2.0x = 200%)"
    )
    night_shift_overtime_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.50,
        validators=[MinValueValidator(1.00), MaxValueValidator(5.00)],
        help_text="Pay rate multiplier for night shift overtime (KSA default: 1.5x)"
    )

    # Weekend Work Compensation (KSA: mandatory compensatory day off)
    weekend_work_requires_compensatory_day = models.BooleanField(
        default=True,
        help_text="KSA: Weekend work requires compensatory day off in addition to pay"
    )

    # Approval Requirements
    requires_manager_approval = models.BooleanField(
        default=True,
        help_text="Overtime must be pre-approved by manager"
    )
    requires_hr_approval = models.BooleanField(
        default=False,
        help_text="Overtime requires HR approval in addition to manager"
    )
    allow_retroactive_requests = models.BooleanField(
        default=False,
        help_text="Allow overtime requests after work is completed"
    )
    max_days_advance_request = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        help_text="Maximum days in advance for overtime requests"
    )

    # Night Shift Definition
    night_shift_start_time = models.TimeField(
        default="22:00",
        help_text="Start time for night shift (KSA typically 22:00-06:00)"
    )
    night_shift_end_time = models.TimeField(
        default="06:00",
        help_text="End time for night shift"
    )

    # Notes
    policy_notes = models.TextField(
        blank=True,
        help_text="Additional policy notes and guidelines"
    )

    effective_from = models.DateField(
        default=timezone.now,
        help_text="Date when this configuration becomes effective"
    )
    effective_to = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this configuration expires (optional)"
    )

    class Meta:
        db_table = 'hr_overtime_configuration'
        verbose_name = 'Overtime Configuration'
        verbose_name_plural = 'Overtime Configurations'
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.configuration_name} (Effective: {self.effective_from})"

    def save(self, *args, **kwargs):
        """Ensure only one active configuration"""
        if self.is_active:
            # Deactivate all other configurations
            OvertimeConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active_config(cls):
        """Get the currently active overtime configuration"""
        config = cls.objects.filter(is_active=True).first()
        if not config:
            # Create default configuration
            config = cls.objects.create(
                configuration_name="Saudi Arabia Labor Law Defaults",
                is_active=True
            )
        return config

    def get_rate_for_overtime_type(self, overtime_type):
        """Get pay rate multiplier for specific overtime type"""
        from floor_app.operations.hr.models.attendance import OvertimeType

        rate_mapping = {
            OvertimeType.REGULAR: self.regular_overtime_rate,
            OvertimeType.WEEKEND: self.weekend_overtime_rate,
            OvertimeType.HOLIDAY: self.holiday_overtime_rate,
            OvertimeType.NIGHT: self.night_shift_overtime_rate,
        }
        return rate_mapping.get(overtime_type, self.regular_overtime_rate)


class AttendanceConfiguration(AuditMixin):
    """
    Configurable attendance tracking settings
    """
    is_active = models.BooleanField(default=True)
    configuration_name = models.CharField(max_length=100, default="Default Attendance Policy")

    # Working Hours (KSA standard: 48 hours/week or 8 hours/day)
    standard_working_hours_per_day = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=8.00,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Standard working hours per day (KSA: 8 hours)"
    )
    standard_working_hours_per_week = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=48.00,
        validators=[MinValueValidator(1), MaxValueValidator(70)],
        help_text="Standard working hours per week (KSA: 48 hours)"
    )

    # Ramadan Hours (KSA: 6 hours/day for Muslims during Ramadan)
    ramadan_working_hours_per_day = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=6.00,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Working hours during Ramadan (KSA: 6 hours for Muslims)"
    )
    apply_ramadan_hours = models.BooleanField(
        default=True,
        help_text="Automatically apply reduced hours during Ramadan"
    )

    # Grace Periods
    late_arrival_grace_minutes = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        help_text="Grace period for late arrival (minutes)"
    )
    early_departure_grace_minutes = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        help_text="Grace period for early departure (minutes)"
    )

    # Break Times
    default_break_duration_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(180)],
        help_text="Default break/lunch duration (minutes)"
    )
    break_time_paid = models.BooleanField(
        default=False,
        help_text="Whether break time is included in paid hours"
    )

    # Delay Thresholds
    minor_delay_threshold_minutes = models.IntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text="Threshold for minor delay (warning only)"
    )
    major_delay_threshold_minutes = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(240)],
        help_text="Threshold for major delay (disciplinary action)"
    )

    # Absence Policies
    consecutive_absences_trigger = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Number of consecutive absences to trigger alert"
    )

    # Punch Machine Settings
    allow_manual_entry = models.BooleanField(
        default=True,
        help_text="Allow manual attendance entry for employees without punch machines"
    )
    require_supervisor_approval_manual_entry = models.BooleanField(
        default=True,
        help_text="Manual entries require supervisor approval"
    )

    effective_from = models.DateField(default=timezone.now)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'hr_attendance_configuration'
        verbose_name = 'Attendance Configuration'
        verbose_name_plural = 'Attendance Configurations'
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.configuration_name} (Effective: {self.effective_from})"

    def save(self, *args, **kwargs):
        if self.is_active:
            AttendanceConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active_config(cls):
        """Get the currently active attendance configuration"""
        config = cls.objects.filter(is_active=True).first()
        if not config:
            config = cls.objects.create(
                configuration_name="Saudi Arabia Standard Policy",
                is_active=True
            )
        return config


class DelayReason(models.TextChoices):
    """Standardized reasons for delay/late arrival"""
    TRAFFIC = 'TRAFFIC', 'Traffic Congestion'
    TRANSPORTATION = 'TRANSPORTATION', 'Transportation Issues'
    FAMILY_EMERGENCY = 'FAMILY_EMERGENCY', 'Family Emergency'
    MEDICAL = 'MEDICAL', 'Medical Appointment/Issue'
    WEATHER = 'WEATHER', 'Weather Conditions'
    VEHICLE_BREAKDOWN = 'VEHICLE_BREAKDOWN', 'Vehicle Breakdown'
    OVERSLEPT = 'OVERSLEPT', 'Overslept'
    PERSONAL = 'PERSONAL', 'Personal Reasons'
    OTHER = 'OTHER', 'Other (Specify in notes)'


class DelayIncident(AuditMixin):
    """
    Records of employee delays/late arrivals
    """
    employee = models.ForeignKey(
        'HREmployee',
        on_delete=models.CASCADE,
        related_name='delay_incidents'
    )
    date = models.DateField(db_index=True)

    # Time Details
    scheduled_time = models.TimeField(help_text="Scheduled arrival time")
    actual_time = models.TimeField(help_text="Actual arrival time")
    delay_minutes = models.IntegerField(
        default=0,
        help_text="Minutes late (calculated automatically)"
    )

    # Reason and Justification
    delay_reason = models.CharField(
        max_length=20,
        choices=DelayReason.choices,
        default=DelayReason.OTHER
    )
    employee_explanation = models.TextField(
        blank=True,
        help_text="Employee's explanation for the delay"
    )
    has_valid_excuse = models.BooleanField(
        default=False,
        help_text="Manager determined excuse is valid"
    )

    # Supporting Documentation
    supporting_document = models.FileField(
        upload_to='hr/delay_documents/%Y/%m/',
        null=True,
        blank=True,
        help_text="Supporting document (medical cert, accident report, etc.)"
    )

    # Classification
    severity = models.CharField(
        max_length=10,
        choices=[
            ('MINOR', 'Minor Delay'),
            ('MAJOR', 'Major Delay'),
            ('SEVERE', 'Severe Delay'),
        ],
        default='MINOR'
    )

    # Manager Review
    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_delays'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    manager_notes = models.TextField(blank=True)

    # Disciplinary Action
    disciplinary_action_taken = models.BooleanField(default=False)
    action_description = models.TextField(blank=True)

    class Meta:
        db_table = 'hr_delay_incident'
        verbose_name = 'Delay Incident'
        verbose_name_plural = 'Delay Incidents'
        unique_together = [['employee', 'date']]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['employee', 'date'], name='ix_delay_emp_date'),
            models.Index(fields=['date', 'severity'], name='ix_delay_date_severity'),
        ]

    def __str__(self):
        return f"{self.employee.employee_no} - {self.date} - {self.delay_minutes} min"

    def save(self, *args, **kwargs):
        """Auto-calculate delay minutes and severity"""
        if self.scheduled_time and self.actual_time:
            from datetime import datetime, timedelta

            scheduled = datetime.combine(self.date, self.scheduled_time)
            actual = datetime.combine(self.date, self.actual_time)

            if actual > scheduled:
                self.delay_minutes = int((actual - scheduled).total_seconds() / 60)

            # Auto-classify severity based on configuration
            config = AttendanceConfiguration.get_active_config()
            if self.delay_minutes >= config.major_delay_threshold_minutes:
                self.severity = 'MAJOR'
            elif self.delay_minutes >= config.minor_delay_threshold_minutes:
                self.severity = 'MINOR'
            else:
                self.severity = 'MINOR'

        super().save(*args, **kwargs)
