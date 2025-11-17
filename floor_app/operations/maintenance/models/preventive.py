"""
Preventive Maintenance (PM) Models

Models for planning and scheduling preventive maintenance tasks.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin
from .asset import Asset, AssetCategory


class PMPlan(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    PM Plan/Template defining what maintenance to do and how often.
    Can apply to specific assets or entire asset categories.
    """

    FREQUENCY_TYPE_CHOICES = (
        ('TIME_BASED', 'Time Based'),
        ('METER_BASED', 'Meter Based'),
        ('CONDITION_BASED', 'Condition Based'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    # Identification
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique PM plan code (e.g., PM-GRND-30D)"
    )
    name = models.CharField(
        max_length=200,
        help_text="PM plan name"
    )
    description = models.TextField(
        help_text="Overview of this maintenance plan"
    )

    # What to do - detailed instructions
    tasks_description = models.TextField(
        help_text="Detailed step-by-step tasks to perform"
    )
    safety_instructions = models.TextField(
        blank=True,
        default="",
        help_text="Safety precautions and PPE requirements"
    )
    tools_required = models.TextField(
        blank=True,
        default="",
        help_text="Tools and equipment needed"
    )
    spare_parts_list = models.TextField(
        blank=True,
        default="",
        help_text="List of typical spare parts that may be needed"
    )

    # Who should do it
    required_skill_level = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Required skill level or certification"
    )
    minimum_technicians = models.PositiveIntegerField(
        default=1,
        help_text="Minimum number of technicians required"
    )

    # Time estimates
    estimated_duration_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Estimated time to complete in minutes"
    )

    # Priority
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        help_text="Default priority for tasks generated from this plan"
    )

    # Frequency configuration
    frequency_type = models.CharField(
        max_length=20,
        choices=FREQUENCY_TYPE_CHOICES,
        default='TIME_BASED',
        help_text="How frequency is determined"
    )
    interval_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Interval in days for time-based PM"
    )
    interval_meter_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Meter reading interval for meter-based PM"
    )

    # Scope - what assets this plan applies to
    applies_to_category = models.ForeignKey(
        AssetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pm_plans',
        help_text="Apply to all assets in this category"
    )
    applies_to_specific_assets = models.ManyToManyField(
        Asset,
        blank=True,
        related_name='specific_pm_plans',
        help_text="Apply to these specific assets"
    )

    # Control
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this plan is currently active"
    )

    # Advance scheduling
    generate_days_before = models.PositiveIntegerField(
        default=7,
        help_text="Generate task this many days before due date"
    )

    # Reference to knowledge/instructions
    instruction_document_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to Knowledge module instruction document"
    )

    class Meta:
        db_table = "maintenance_pm_plan"
        verbose_name = "PM Plan"
        verbose_name_plural = "PM Plans"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code'], name='ix_maint_pmplan_code'),
            models.Index(fields=['is_active'], name='ix_maint_pmplan_active'),
            models.Index(fields=['frequency_type'], name='ix_maint_pmplan_freq'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def estimated_duration_display(self):
        """Human-readable duration."""
        if self.estimated_duration_minutes < 60:
            return f"{self.estimated_duration_minutes} min"
        hours = self.estimated_duration_minutes // 60
        minutes = self.estimated_duration_minutes % 60
        if minutes:
            return f"{hours}h {minutes}m"
        return f"{hours}h"

    @property
    def frequency_display(self):
        """Human-readable frequency."""
        if self.frequency_type == 'TIME_BASED' and self.interval_days:
            if self.interval_days == 1:
                return "Daily"
            elif self.interval_days == 7:
                return "Weekly"
            elif self.interval_days == 14:
                return "Bi-weekly"
            elif self.interval_days == 30:
                return "Monthly"
            elif self.interval_days == 90:
                return "Quarterly"
            elif self.interval_days == 180:
                return "Semi-annually"
            elif self.interval_days == 365:
                return "Annually"
            else:
                return f"Every {self.interval_days} days"
        elif self.frequency_type == 'METER_BASED' and self.interval_meter_value:
            return f"Every {self.interval_meter_value} units"
        return self.get_frequency_type_display()


class PMSchedule(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Specific PM schedule for an asset based on a plan.
    Tracks when PM is due for each asset-plan combination.
    """

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='pm_schedules',
        help_text="Asset this schedule is for"
    )
    pm_plan = models.ForeignKey(
        PMPlan,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="PM plan this schedule follows"
    )

    # Schedule timing
    next_due_date = models.DateField(
        db_index=True,
        help_text="Next scheduled PM date"
    )
    last_completed_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last completed PM"
    )

    # For meter-based PM
    next_due_meter_reading = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Meter reading when next PM is due"
    )
    last_meter_reading_at_pm = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Meter reading at last PM"
    )

    # Control
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this schedule is active"
    )

    # Override settings
    custom_interval_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override the plan's interval for this specific asset"
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes about this specific schedule"
    )

    class Meta:
        db_table = "maintenance_pm_schedule"
        verbose_name = "PM Schedule"
        verbose_name_plural = "PM Schedules"
        ordering = ['next_due_date']
        unique_together = [['asset', 'pm_plan']]
        indexes = [
            models.Index(fields=['next_due_date'], name='ix_maint_pmsched_due'),
            models.Index(fields=['asset', 'is_active'], name='ix_maint_pmsched_asset'),
            models.Index(fields=['is_active', 'next_due_date'], name='ix_maint_pmsched_act_due'),
        ]

    def __str__(self):
        return f"{self.asset.asset_code} - {self.pm_plan.code} (Due: {self.next_due_date})"

    @property
    def is_overdue(self):
        """Check if PM is overdue."""
        return self.next_due_date < timezone.now().date()

    @property
    def days_until_due(self):
        """Days until PM is due (negative if overdue)."""
        delta = self.next_due_date - timezone.now().date()
        return delta.days

    @property
    def status_display(self):
        """Status text."""
        days = self.days_until_due
        if days < 0:
            return f"OVERDUE by {abs(days)} days"
        elif days == 0:
            return "Due TODAY"
        elif days <= 7:
            return f"Due in {days} days"
        else:
            return f"Scheduled ({self.next_due_date})"

    @property
    def status_class(self):
        """Bootstrap class for status."""
        days = self.days_until_due
        if days < 0:
            return "danger"
        elif days == 0:
            return "warning"
        elif days <= 7:
            return "info"
        else:
            return "success"

    def calculate_next_due_date(self, completed_date=None):
        """Calculate next due date after completion."""
        if completed_date is None:
            completed_date = timezone.now().date()

        # Use custom interval if set, otherwise use plan's interval
        interval = self.custom_interval_days or self.pm_plan.interval_days

        if self.pm_plan.frequency_type == 'TIME_BASED' and interval:
            from datetime import timedelta
            self.last_completed_date = completed_date
            self.next_due_date = completed_date + timedelta(days=interval)
        elif self.pm_plan.frequency_type == 'METER_BASED':
            # For meter-based, next_due_date should be updated based on meter reading
            self.last_completed_date = completed_date
            if self.asset.current_meter_reading and self.pm_plan.interval_meter_value:
                self.last_meter_reading_at_pm = self.asset.current_meter_reading
                self.next_due_meter_reading = (
                    self.asset.current_meter_reading + self.pm_plan.interval_meter_value
                )


class PMTask(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Actual PM task instance - the work to be done.
    Generated from PMSchedule when due.
    """

    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('SKIPPED', 'Skipped'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    # Link to schedule
    schedule = models.ForeignKey(
        PMSchedule,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text="PM schedule this task belongs to"
    )

    # Task identification
    task_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique task number (e.g., PMT-2025-0001)"
    )

    # Status and priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED',
        db_index=True,
        help_text="Current task status"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        db_index=True,
        help_text="Task priority"
    )

    # Timing
    scheduled_date = models.DateField(
        db_index=True,
        help_text="Date task is scheduled for"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date (if different from scheduled)"
    )
    actual_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work actually started"
    )
    actual_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work was completed"
    )
    actual_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Actual time spent in minutes"
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_pm_tasks',
        help_text="User assigned to this task"
    )
    performed_by_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="HR Employee who performed the task"
    )
    performed_by_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Name of person who performed task (denormalized)"
    )

    # Results
    completion_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes about what was done"
    )
    issues_found = models.TextField(
        blank=True,
        default="",
        help_text="Any issues discovered during PM"
    )
    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether follow-up work is needed"
    )
    follow_up_notes = models.TextField(
        blank=True,
        default="",
        help_text="Details about required follow-up"
    )

    # Meter reading at completion
    meter_reading_at_completion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Meter reading when task was completed"
    )

    # Cancellation/Skip reason
    cancellation_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason if task was cancelled or skipped"
    )

    class Meta:
        db_table = "maintenance_pm_task"
        verbose_name = "PM Task"
        verbose_name_plural = "PM Tasks"
        ordering = ['-scheduled_date', '-created_at']
        indexes = [
            models.Index(fields=['task_number'], name='ix_maint_pmtask_num'),
            models.Index(fields=['status', 'scheduled_date'], name='ix_maint_pmtask_stat_sched'),
            models.Index(fields=['status', 'priority'], name='ix_maint_pmtask_stat_prio'),
            models.Index(fields=['assigned_to', 'status'], name='ix_maint_pmtask_assigned'),
        ]

    def __str__(self):
        return f"{self.task_number} - {self.schedule.asset.asset_code}"

    @property
    def asset(self):
        """Convenience accessor for the asset."""
        return self.schedule.asset

    @property
    def pm_plan(self):
        """Convenience accessor for the PM plan."""
        return self.schedule.pm_plan

    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.status in ['COMPLETED', 'CANCELLED', 'SKIPPED']:
            return False
        target_date = self.due_date or self.scheduled_date
        return target_date < timezone.now().date()

    @property
    def status_display_class(self):
        """Bootstrap class for status badge."""
        mapping = {
            'SCHEDULED': 'info',
            'IN_PROGRESS': 'warning',
            'COMPLETED': 'success',
            'CANCELLED': 'secondary',
            'SKIPPED': 'dark',
        }
        return mapping.get(self.status, 'secondary')

    def start_task(self, user=None):
        """Start working on the task."""
        self.status = 'IN_PROGRESS'
        self.actual_start = timezone.now()
        if user:
            self.performed_by_name = user.get_full_name() or user.username
        self.save(update_fields=['status', 'actual_start', 'performed_by_name', 'updated_at'])

    def complete_task(self, notes="", issues="", follow_up=False):
        """Complete the task."""
        self.status = 'COMPLETED'
        self.actual_end = timezone.now()
        if self.actual_start:
            delta = self.actual_end - self.actual_start
            self.actual_duration_minutes = int(delta.total_seconds() / 60)
        self.completion_notes = notes
        self.issues_found = issues
        self.follow_up_required = follow_up

        # Update the schedule's next due date
        self.schedule.calculate_next_due_date(completed_date=timezone.now().date())
        self.schedule.save()

        # Update asset's last maintenance date
        self.asset.last_maintenance_date = timezone.now().date()
        self.asset.save(update_fields=['last_maintenance_date', 'updated_at'])

        self.save()

    def cancel_task(self, reason=""):
        """Cancel the task."""
        self.status = 'CANCELLED'
        self.cancellation_reason = reason
        self.save(update_fields=['status', 'cancellation_reason', 'updated_at'])

    def skip_task(self, reason=""):
        """Skip the task (reschedule without doing it)."""
        self.status = 'SKIPPED'
        self.cancellation_reason = reason

        # Update schedule to next interval
        self.schedule.calculate_next_due_date()
        self.schedule.save()

        self.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
