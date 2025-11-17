"""
Routing & Operations Layer

Tracks the sequence of operations (process steps) for each job card.
Captures time per step and operator assignments.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin


class JobRoute(AuditMixin):
    """
    Route header for a job card.

    Each job card has one route that defines its processing sequence.
    """

    job_card = models.OneToOneField(
        'JobCard',
        on_delete=models.CASCADE,
        related_name='route',
        help_text="Job card this route belongs to"
    )

    # Route metadata
    template_used = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Template used to generate this route"
    )

    # Totals (computed fields)
    total_planned_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total planned hours for all steps"
    )
    total_actual_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total actual hours spent"
    )

    is_complete = models.BooleanField(
        default=False,
        db_index=True,
        help_text="All steps completed"
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="Route-level notes"
    )

    class Meta:
        db_table = "production_job_route"
        verbose_name = "Job Route"
        verbose_name_plural = "Job Routes"
        indexes = [
            models.Index(fields=['job_card'], name='ix_route_jc'),
            models.Index(fields=['is_complete'], name='ix_route_complete'),
        ]

    def __str__(self):
        return f"Route for {self.job_card.job_card_number}"

    def calculate_totals(self):
        """Recalculate total hours from steps."""
        from django.db.models import Sum

        # Planned hours
        planned = self.steps.aggregate(
            total=Sum('planned_duration_hours')
        )['total'] or 0
        self.total_planned_hours = planned

        # Actual hours (sum of completed steps)
        actual = 0
        for step in self.steps.filter(status='DONE'):
            if step.actual_duration_hours:
                actual += step.actual_duration_hours
        self.total_actual_hours = actual

        # Check completion
        total_steps = self.steps.count()
        done_steps = self.steps.filter(status='DONE').count()
        self.is_complete = (total_steps > 0 and done_steps == total_steps)

        self.save(update_fields=['total_planned_hours', 'total_actual_hours', 'is_complete', 'updated_at'])

    @property
    def current_step(self):
        """Get the current in-progress step."""
        return self.steps.filter(status='IN_PROGRESS').first()

    @property
    def next_step(self):
        """Get the next step to be started."""
        return self.steps.filter(status='NOT_STARTED').order_by('sequence').first()

    @property
    def completion_percentage(self):
        """Calculate route completion percentage."""
        total = self.steps.count()
        if total > 0:
            done = self.steps.filter(status='DONE').count()
            return round((done / total) * 100, 1)
        return 0


class JobRouteStep(AuditMixin):
    """
    Individual operation step within a job route.

    Tracks planned and actual timing, operator assignment, and status.
    This is the core model for time tracking and KPI calculation.
    """

    STATUS_CHOICES = (
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('PAUSED', 'Paused'),
        ('DONE', 'Done'),
        ('SKIPPED', 'Skipped'),
        ('BLOCKED', 'Blocked'),
    )

    route = models.ForeignKey(
        JobRoute,
        on_delete=models.CASCADE,
        related_name='steps',
        help_text="Parent route"
    )

    operation = models.ForeignKey(
        'OperationDefinition',
        on_delete=models.PROTECT,
        related_name='route_steps',
        help_text="Operation to perform"
    )

    sequence = models.IntegerField(
        default=10,
        help_text="Order in route (10, 20, 30...)"
    )

    # Planning
    planned_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Planned start time"
    )
    planned_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Planned end time"
    )
    planned_duration_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Planned duration in hours"
    )

    # Actual timing
    actual_start_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When step actually started"
    )
    actual_end_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When step actually ended"
    )

    # Pause tracking (for accurate time)
    paused_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When step was paused"
    )
    total_pause_minutes = models.IntegerField(
        default=0,
        help_text="Total pause duration in minutes"
    )

    # Assignment
    operator = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='route_steps_as_operator',
        help_text="Operator performing the step"
    )
    supervisor = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='route_steps_as_supervisor',
        help_text="Supervisor overseeing the step"
    )

    # Approval (if required)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_route_steps',
        help_text="User who approved this step"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When step was approved"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOT_STARTED',
        db_index=True
    )

    # Results/Output
    result_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes/results from this step"
    )
    quality_check_passed = models.BooleanField(
        null=True,
        blank=True,
        help_text="Quality check result (if applicable)"
    )

    # Blocking info
    blocked_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for blocking"
    )

    # Component consumption (future integration)
    # Will link to inventory transactions for material consumption

    class Meta:
        db_table = "production_job_route_step"
        verbose_name = "Job Route Step"
        verbose_name_plural = "Job Route Steps"
        ordering = ['route', 'sequence']
        indexes = [
            models.Index(fields=['route', 'sequence'], name='ix_step_route_seq'),
            models.Index(fields=['status'], name='ix_step_status'),
            models.Index(fields=['operator'], name='ix_step_operator'),
            models.Index(fields=['actual_start_at'], name='ix_step_start'),
        ]

    def __str__(self):
        return f"{self.route.job_card.job_card_number} - #{self.sequence} {self.operation.code}"

    @property
    def actual_duration_hours(self):
        """Calculate actual duration in hours (excluding pause time)."""
        if self.actual_start_at and self.actual_end_at:
            delta = self.actual_end_at - self.actual_start_at
            total_seconds = delta.total_seconds()
            pause_seconds = self.total_pause_minutes * 60
            net_seconds = total_seconds - pause_seconds
            return round(net_seconds / 3600, 2)
        return None

    @property
    def is_overdue(self):
        """Check if step is overdue based on planned end."""
        if self.planned_end and self.status not in ('DONE', 'SKIPPED'):
            return timezone.now() > self.planned_end
        return False

    @property
    def wait_time_from_previous(self):
        """
        Calculate wait time between end of previous step and start of this step.
        Returns time in hours.
        """
        if not self.actual_start_at:
            return None

        # Get previous step
        previous_step = self.route.steps.filter(
            sequence__lt=self.sequence
        ).order_by('-sequence').first()

        if previous_step and previous_step.actual_end_at:
            delta = self.actual_start_at - previous_step.actual_end_at
            return round(delta.total_seconds() / 3600, 2)

        return None

    def start_step(self, operator=None):
        """Mark step as started."""
        self.status = 'IN_PROGRESS'
        self.actual_start_at = timezone.now()
        if operator:
            self.operator = operator
        self.save(update_fields=['status', 'actual_start_at', 'operator', 'updated_at'])

    def pause_step(self):
        """Pause the step."""
        if self.status == 'IN_PROGRESS':
            self.status = 'PAUSED'
            self.paused_at = timezone.now()
            self.save(update_fields=['status', 'paused_at', 'updated_at'])

    def resume_step(self):
        """Resume a paused step."""
        if self.status == 'PAUSED' and self.paused_at:
            delta = timezone.now() - self.paused_at
            self.total_pause_minutes += int(delta.total_seconds() / 60)
            self.status = 'IN_PROGRESS'
            self.paused_at = None
            self.save(update_fields=['status', 'paused_at', 'total_pause_minutes', 'updated_at'])

    def complete_step(self, operator=None, result_notes=''):
        """Mark step as completed."""
        # If was paused, add final pause time
        if self.status == 'PAUSED' and self.paused_at:
            delta = timezone.now() - self.paused_at
            self.total_pause_minutes += int(delta.total_seconds() / 60)

        self.status = 'DONE'
        self.actual_end_at = timezone.now()
        if operator:
            self.operator = operator
        if result_notes:
            self.result_notes = result_notes
        self.paused_at = None

        self.save(update_fields=[
            'status', 'actual_end_at', 'operator', 'result_notes',
            'total_pause_minutes', 'paused_at', 'updated_at'
        ])

        # Update route totals
        self.route.calculate_totals()

    def skip_step(self, reason=''):
        """Skip this step (e.g., not required for this job)."""
        self.status = 'SKIPPED'
        self.result_notes = f"SKIPPED: {reason}"
        self.save(update_fields=['status', 'result_notes', 'updated_at'])

        # Update route totals
        self.route.calculate_totals()

    def block_step(self, reason=''):
        """Block this step due to an issue."""
        self.status = 'BLOCKED'
        self.blocked_reason = reason
        self.save(update_fields=['status', 'blocked_reason', 'updated_at'])

    def approve_step(self, user):
        """Approve this step (if supervisor approval required)."""
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=['approved_by', 'approved_at', 'updated_at'])
