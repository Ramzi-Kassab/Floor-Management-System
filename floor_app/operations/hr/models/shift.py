"""
HR Shift Management Models

Manages shift templates, schedules, and shift assignments.
"""
from django.db import models
from django.core.exceptions import ValidationError


class HRShiftTemplate(models.Model):
    """
    Shift template model.

    Defines reusable shift templates (e.g., Day Shift, Night Shift)
    that can be assigned to employees.
    """

    DAYS_OF_WEEK = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    # Shift details
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique shift code (e.g., DAY-01, NIGHT-01)'
    )

    name = models.CharField(
        max_length=100,
        help_text='Shift name (e.g., Day Shift, Night Shift, Morning Shift)'
    )

    description = models.TextField(
        blank=True,
        help_text='Shift description'
    )

    # Timing
    start_time = models.TimeField(
        help_text='Shift start time'
    )

    end_time = models.TimeField(
        help_text='Shift end time'
    )

    # Duration in hours (calculated or manual)
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text='Shift duration in hours'
    )

    # Shift classification
    is_night_shift = models.BooleanField(
        default=False,
        help_text='Is this a night shift?'
    )

    # Working days (stored as JSON array)
    working_days = models.JSONField(
        default=list,
        help_text='Days of the week this shift applies to (JSON array of day codes)'
    )

    # Break time
    break_duration_minutes = models.IntegerField(
        default=30,
        help_text='Break duration in minutes'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Is this shift template active?'
    )

    # Department/Location restriction (optional)
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shift_templates',
        help_text='Department this shift is for (optional)'
    )

    # Cost center (for tracking)
    cost_center = models.ForeignKey(
        'core.CostCenter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shift_templates',
        help_text='Cost center for this shift'
    )

    # Overtime multiplier
    overtime_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.0,
        help_text='Overtime rate multiplier for this shift'
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_shift_templates'
    )

    class Meta:
        db_table = 'hr_shift_template'
        verbose_name = 'Shift Template'
        verbose_name_plural = 'Shift Templates'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        """Validate shift template."""
        # Validate working_days is a list
        if not isinstance(self.working_days, list):
            raise ValidationError({'working_days': 'Working days must be a list'})

        # Validate day codes
        valid_days = [day[0] for day in self.DAYS_OF_WEEK]
        for day in self.working_days:
            if day not in valid_days:
                raise ValidationError({
                    'working_days': f'Invalid day code: {day}. Must be one of {valid_days}'
                })

    def get_working_days_display(self):
        """Get human-readable working days."""
        day_map = dict(self.DAYS_OF_WEEK)
        return [day_map.get(day, day) for day in self.working_days]

    @property
    def is_overnight_shift(self):
        """Check if shift crosses midnight."""
        return self.end_time < self.start_time

    def save(self, *args, **kwargs):
        # Calculate duration if not provided
        if not self.duration_hours:
            from datetime import datetime, timedelta

            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)

            # Handle overnight shifts
            if self.end_time < self.start_time:
                end += timedelta(days=1)

            duration = (end - start).total_seconds() / 3600
            self.duration_hours = duration

        super().save(*args, **kwargs)


class ShiftAssignment(models.Model):
    """
    Shift assignment model.

    Links employees to shift templates for specific periods.
    """

    # Employee and shift
    employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        related_name='shift_assignments',
        help_text='Employee assigned to this shift'
    )

    shift_template = models.ForeignKey(
        HRShiftTemplate,
        on_delete=models.PROTECT,
        related_name='assignments',
        help_text='Shift template'
    )

    # Assignment period
    start_date = models.DateField(
        help_text='Assignment start date'
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        help_text='Assignment end date (null for ongoing)'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Is this assignment active?'
    )

    notes = models.TextField(
        blank=True,
        help_text='Assignment notes'
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_shift_assignments'
    )

    class Meta:
        db_table = 'hr_shift_assignment'
        verbose_name = 'Shift Assignment'
        verbose_name_plural = 'Shift Assignments'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['employee', 'is_active']),
            models.Index(fields=['shift_template']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.employee.employee_code} - {self.shift_template.name} ({self.start_date})"

    def clean(self):
        """Validate shift assignment."""
        # Validate date range
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date cannot be before start date'})

        # Check for overlapping assignments
        overlapping = ShiftAssignment.objects.filter(
            employee=self.employee,
            is_active=True
        ).exclude(pk=self.pk)

        if self.end_date:
            overlapping = overlapping.filter(
                models.Q(start_date__lte=self.end_date, end_date__gte=self.start_date) |
                models.Q(start_date__lte=self.end_date, end_date__isnull=True)
            )
        else:
            overlapping = overlapping.filter(
                models.Q(end_date__gte=self.start_date) |
                models.Q(end_date__isnull=True)
            )

        if overlapping.exists():
            raise ValidationError('Employee already has an active shift assignment for this period')

    @property
    def is_current(self):
        """Check if assignment is currently active."""
        from django.utils import timezone
        today = timezone.now().date()

        if not self.is_active:
            return False

        if self.start_date > today:
            return False

        if self.end_date and self.end_date < today:
            return False

        return True
