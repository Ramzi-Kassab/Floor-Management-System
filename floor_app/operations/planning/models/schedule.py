"""
Planning & KPI - Schedule Management
Production schedules and scheduled operations.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .resource import ResourceType


class ProductionSchedule(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Master schedule container.
    Groups scheduled operations for a planning period.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('FROZEN', 'Frozen - No Changes'),
        ('SUPERSEDED', 'Superseded by New Schedule'),
    ]

    ALGORITHM_CHOICES = [
        ('EARLIEST_DUE_DATE', 'Earliest Due Date First'),
        ('SHORTEST_JOB_FIRST', 'Shortest Job First'),
        ('CRITICAL_RATIO', 'Critical Ratio'),
        ('PRIORITY_WEIGHTED', 'Priority Weighted'),
        ('MANUAL', 'Manual Scheduling'),
    ]

    name = models.CharField(max_length=200)
    schedule_date = models.DateField(
        help_text="Schedule effective date"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )

    planning_horizon_days = models.PositiveIntegerField(
        default=30,
        help_text="Number of days this schedule covers"
    )

    # Scheduling parameters
    scheduling_algorithm = models.CharField(
        max_length=50,
        choices=ALGORITHM_CHOICES,
        default='EARLIEST_DUE_DATE'
    )
    priority_weighting = models.JSONField(
        default=dict,
        help_text="Priority weights (e.g., {'CRITICAL': 1.0, 'RUSH': 0.8})"
    )

    # Workflow
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='schedules_created'
    )
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='schedules_published'
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "planning_production_schedule"
        verbose_name = "Production Schedule"
        verbose_name_plural = "Production Schedules"
        ordering = ['-schedule_date', '-created_at']
        indexes = [
            models.Index(fields=['schedule_date'], name='ix_plan_sched_date'),
            models.Index(fields=['status'], name='ix_plan_sched_status'),
        ]

    def __str__(self):
        return f"{self.name} - {self.schedule_date}"

    def publish(self, user):
        """Publish the schedule for execution."""
        if self.status != 'DRAFT':
            raise ValueError("Only draft schedules can be published")

        self.status = 'PUBLISHED'
        self.published_at = timezone.now()
        self.published_by = user
        self.save()

    def freeze(self):
        """Freeze the schedule to prevent changes."""
        self.status = 'FROZEN'
        self.save()

    def supersede(self):
        """Mark as superseded by a new schedule."""
        self.status = 'SUPERSEDED'
        self.save()

    @property
    def operation_count(self):
        """Count of scheduled operations."""
        return self.scheduled_operations.count()

    @property
    def is_editable(self):
        """Check if schedule can be modified."""
        return self.status == 'DRAFT'


class ScheduledOperation(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Individual scheduled operations within a production schedule.
    Links job cards and route steps to specific time slots and resources.
    """
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('RELEASED', 'Released to Shop Floor'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING', 'Waiting'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    DELAY_CATEGORY_CHOICES = [
        ('MATERIAL', 'Material Shortage'),
        ('EQUIPMENT', 'Equipment Issue'),
        ('QUALITY', 'Quality Hold'),
        ('LABOR', 'Labor Shortage'),
        ('EXTERNAL', 'External Dependency'),
        ('OTHER', 'Other'),
    ]

    schedule = models.ForeignKey(
        ProductionSchedule,
        on_delete=models.CASCADE,
        related_name='scheduled_operations'
    )

    # What is being scheduled (loose coupling)
    job_card_id = models.BigIntegerField(
        db_index=True,
        help_text="Reference to production.JobCard"
    )
    job_route_step_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to production.JobRouteStep"
    )
    operation_code = models.CharField(
        max_length=50,
        help_text="Operation code from OperationDefinition"
    )

    # Schedule timing
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    planned_duration_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    # Resource assignment
    resource_type = models.ForeignKey(
        ResourceType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='scheduled_operations'
    )
    assigned_asset_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to maintenance.Asset"
    )
    assigned_employee_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to hr.HREmployee"
    )

    # Priority and sequence
    sequence_number = models.PositiveIntegerField(default=0)
    priority_score = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Calculated priority score for scheduling"
    )

    # Constraints
    earliest_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cannot start before this time (predecessor constraint)"
    )
    latest_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Must finish by this time (customer due date)"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNED',
        db_index=True
    )

    # Actual execution (updated from shop floor)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    actual_duration_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Delays and issues
    is_delayed = models.BooleanField(default=False)
    delay_reason = models.CharField(max_length=200, blank=True, default="")
    delay_category = models.CharField(
        max_length=50,
        choices=DELAY_CATEGORY_CHOICES,
        blank=True,
        default=""
    )

    # Material readiness
    materials_available = models.BooleanField(default=True)
    materials_shortage_list = models.TextField(
        blank=True,
        default="",
        help_text="JSON list of missing items"
    )

    class Meta:
        db_table = "planning_scheduled_operation"
        verbose_name = "Scheduled Operation"
        verbose_name_plural = "Scheduled Operations"
        ordering = ['schedule', 'planned_start', 'sequence_number']
        indexes = [
            models.Index(fields=['schedule'], name='ix_plan_schedop_sched'),
            models.Index(fields=['job_card_id'], name='ix_plan_schedop_job'),
            models.Index(fields=['status'], name='ix_plan_schedop_status'),
            models.Index(fields=['planned_start'], name='ix_plan_schedop_start'),
            models.Index(
                fields=['resource_type', 'planned_start'],
                name='ix_plan_schedop_res_start'
            ),
            models.Index(fields=['is_delayed'], name='ix_plan_schedop_delayed'),
        ]

    def __str__(self):
        return f"Job #{self.job_card_id} - {self.operation_code}"

    @property
    def variance_hours(self):
        """Calculate variance between planned and actual duration."""
        if self.actual_duration_hours and self.planned_duration_hours:
            return float(self.actual_duration_hours) - float(self.planned_duration_hours)
        return None

    @property
    def is_on_track(self):
        """Check if operation is on track."""
        if self.status == 'COMPLETED':
            return not self.is_delayed
        if self.status in ['PLANNED', 'RELEASED']:
            return not self.is_delayed
        if self.status == 'IN_PROGRESS' and self.actual_start:
            # Check if running late
            expected_end = self.actual_start + timezone.timedelta(
                hours=float(self.planned_duration_hours)
            )
            return timezone.now() <= expected_end
        return False

    def start_operation(self):
        """Mark operation as started."""
        self.status = 'IN_PROGRESS'
        self.actual_start = timezone.now()
        self.save()

    def complete_operation(self):
        """Mark operation as completed."""
        self.status = 'COMPLETED'
        self.actual_end = timezone.now()
        if self.actual_start:
            duration = (self.actual_end - self.actual_start).total_seconds() / 3600
            self.actual_duration_hours = round(duration, 2)
        self.save()

    def mark_delayed(self, reason, category='OTHER'):
        """Mark operation as delayed."""
        self.is_delayed = True
        self.delay_reason = reason
        self.delay_category = category
        self.save()

    def set_waiting(self, reason=""):
        """Put operation on waiting status."""
        self.status = 'WAITING'
        if reason:
            self.delay_reason = reason
        self.save()
