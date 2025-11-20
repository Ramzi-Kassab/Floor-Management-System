"""
Preventive Maintenance models - PM Templates, Schedules, and Tasks.
"""
from django.db import models
from django.conf import settings
from floor_app.mixins import AuditMixin, SoftDeleteMixin
from .asset import Asset, AssetCategory


class PMTemplate(AuditMixin, SoftDeleteMixin, models.Model):
    """Template/plan for preventive maintenance tasks."""

    class FrequencyType(models.TextChoices):
        TIME_BASED = 'TIME_BASED', 'Time-Based (days/weeks/months)'
        METER_BASED = 'METER_BASED', 'Meter-Based (hours/cycles)'
        CONDITION_BASED = 'CONDITION_BASED', 'Condition-Based'

    class SkillLevel(models.TextChoices):
        BASIC = 'BASIC', 'Basic - Any Operator'
        INTERMEDIATE = 'INTERMEDIATE', 'Intermediate - Trained Technician'
        ADVANCED = 'ADVANCED', 'Advanced - Specialist'
        EXPERT = 'EXPERT', 'Expert - Certified Professional'

    code = models.CharField(max_length=50, unique=True, help_text="Template code, e.g., PM-GRN-001")
    name = models.CharField(max_length=255)
    description = models.TextField()
    instructions = models.TextField(help_text="Step-by-step instructions")
    safety_notes = models.TextField(blank=True, help_text="Safety warnings and precautions")
    tools_required = models.TextField(blank=True)
    parts_typically_needed = models.TextField(blank=True)

    # Frequency settings
    frequency_type = models.CharField(
        max_length=20, choices=FrequencyType.choices, default=FrequencyType.TIME_BASED
    )
    frequency_days = models.PositiveIntegerField(
        null=True, blank=True, help_text="Interval in days for time-based PM"
    )
    frequency_hours = models.PositiveIntegerField(
        null=True, blank=True, help_text="Interval in hours for meter-based PM"
    )

    # Duration & Resources
    estimated_duration_minutes = models.PositiveIntegerField(default=60)
    technicians_required = models.PositiveIntegerField(default=1)
    skill_level_required = models.CharField(
        max_length=20, choices=SkillLevel.choices, default=SkillLevel.INTERMEDIATE
    )

    # Applicability
    applies_to_category = models.ForeignKey(
        AssetCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pm_templates', help_text="Apply to all assets of this category"
    )
    applies_to_assets = models.ManyToManyField(
        Asset, blank=True, related_name='assigned_pm_templates',
        help_text="Specific assets (overrides category)"
    )

    # Link to knowledge
    linked_procedure = models.ForeignKey(
        'knowledge.Article', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pm_templates', help_text="Linked SOP/procedure from Knowledge module"
    )

    # Flags
    is_active = models.BooleanField(default=True)
    requires_shutdown = models.BooleanField(default=False, help_text="Asset must be shut down")
    generates_work_order = models.BooleanField(default=True, help_text="Auto-create work order when due")

    class Meta:
        verbose_name = 'PM Template'
        verbose_name_plural = 'PM Templates'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def duration_display(self):
        hours = self.estimated_duration_minutes // 60
        mins = self.estimated_duration_minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"


class PMSchedule(models.Model):
    """Schedule linking PM template to specific asset with timing."""

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='pm_schedules')
    pm_template = models.ForeignKey(PMTemplate, on_delete=models.CASCADE, related_name='schedules', null=True, blank=True)

    # Timing
    last_performed_at = models.DateTimeField(null=True, blank=True)
    next_due_date = models.DateTimeField()

    # Meter-based
    meter_reading_at_last_pm = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    next_due_meter_reading = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_overdue = models.BooleanField(default=False)
    auto_generated = models.BooleanField(default=True, help_text="System-generated vs manual")

    # Override frequency for this specific asset
    custom_frequency_days = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'PM Schedule'
        verbose_name_plural = 'PM Schedules'
        unique_together = [['asset', 'pm_template']]
        ordering = ['next_due_date']
        indexes = [
            models.Index(fields=['next_due_date', 'is_active']),
            models.Index(fields=['is_overdue', 'is_active']),
        ]

    def __str__(self):
        return f"{self.asset.asset_code} - {self.pm_template.code} (Due: {self.next_due_date.date()})"

    def check_overdue(self):
        from django.utils import timezone
        if self.next_due_date < timezone.now():
            self.is_overdue = True
        else:
            self.is_overdue = False
        self.save(update_fields=['is_overdue'])

    @property
    def days_until_due(self):
        from django.utils import timezone
        delta = self.next_due_date - timezone.now()
        return delta.days

    @property
    def frequency_days(self):
        return self.custom_frequency_days or self.pm_template.frequency_days


class PMTask(AuditMixin, models.Model):
    """Actual execution instance of a scheduled PM."""

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        SKIPPED = 'SKIPPED', 'Skipped'
        OVERDUE = 'OVERDUE', 'Overdue'
        CANCELLED = 'CANCELLED', 'Cancelled'

    schedule = models.ForeignKey(PMSchedule, on_delete=models.CASCADE, related_name='tasks')

    # Scheduling
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    # Execution
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    performed_by = models.ForeignKey(
        'hr.HREmployee', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pm_tasks_performed'
    )
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    # Results
    notes = models.TextField(blank=True)
    findings = models.TextField(blank=True, help_text="Issues discovered during PM")
    corrective_action_needed = models.BooleanField(default=False)

    # Meter reading at completion
    meter_reading = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Link to generated work order
    work_order = models.OneToOneField(
        'maintenance.WorkOrder', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='source_pm_task'
    )

    # Next scheduling
    next_due_updated = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'PM Task'
        verbose_name_plural = 'PM Tasks'
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['schedule', 'scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
        ]

    def __str__(self):
        return f"{self.schedule.asset.asset_code} PM on {self.scheduled_date.date()}"

    @property
    def asset(self):
        return self.schedule.asset

    @property
    def pm_template(self):
        return self.schedule.pm_template

    def complete(self, performed_by=None, notes='', findings='', meter_reading=None):
        """Mark PM task as completed and update schedule."""
        from django.utils import timezone
        from datetime import timedelta

        self.status = self.Status.COMPLETED
        if not self.actual_end:
            self.actual_end = timezone.now()
        if performed_by:
            self.performed_by = performed_by
        if notes:
            self.notes = notes
        if findings:
            self.findings = findings
        if meter_reading:
            self.meter_reading = meter_reading

        # Calculate duration
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            self.duration_minutes = int(delta.total_seconds() / 60)

        self.save()

        # Update schedule
        schedule = self.schedule
        schedule.last_performed_at = self.actual_end or timezone.now()
        schedule.is_overdue = False

        # Calculate next due date
        frequency_days = schedule.frequency_days
        if frequency_days:
            schedule.next_due_date = schedule.last_performed_at + timedelta(days=frequency_days)

        if meter_reading:
            schedule.meter_reading_at_last_pm = meter_reading
            if self.pm_template.frequency_hours:
                schedule.next_due_meter_reading = meter_reading + self.pm_template.frequency_hours

        schedule.save()

        # Update asset last_pm_date
        asset = schedule.asset
        asset.last_pm_date = schedule.last_performed_at
        asset.next_pm_date = schedule.next_due_date
        if meter_reading:
            asset.meter_reading = meter_reading
        asset.save(update_fields=['last_pm_date', 'next_pm_date', 'meter_reading'])

        self.next_due_updated = True
        self.save(update_fields=['next_due_updated'])
