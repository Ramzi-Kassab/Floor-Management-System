"""
Visual Planning & WIP Dashboard Models

Provides visual workflow tracking with drag-and-drop kanban-style boards
showing all drill bits in work, their current stage, and bottlenecks.

Replaces Excel manual tracking with live, interactive visual dashboard.
"""

from django.db import models
from django.db.models import Count, Q, F, Sum
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from decimal import Decimal
from floor_app.mixins import AuditMixin, SoftDeleteMixin
import json


class WorkflowStage(AuditMixin):
    """
    Configurable workflow stages for visual kanban board.

    Examples:
    - RECEIVED → INSPECTION → EVAL_QUEUE → EVALUATING → REPAIR_QUEUE →
      REPAIRING → QC → READY_SHIP → SHIPPED

    Each stage has position, color, capacity limits, and business rules.
    """

    STAGE_TYPE_CHOICES = (
        ('QUEUE', 'Queue/Waiting'),
        ('ACTIVE', 'Active Work'),
        ('INSPECTION', 'Inspection/QC'),
        ('HOLD', 'On Hold'),
        ('COMPLETE', 'Complete/Terminal'),
    )

    # Core identification
    stage_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique stage code (e.g., EVAL_QUEUE, REPAIRING)"
    )

    stage_name = models.CharField(
        max_length=100,
        help_text="Display name for stage"
    )

    stage_type = models.CharField(
        max_length=20,
        choices=STAGE_TYPE_CHOICES,
        help_text="Type of stage (affects visualization)"
    )

    # Visual properties
    display_order = models.IntegerField(
        default=10,
        help_text="Display order in kanban (left to right)"
    )

    color_hex = models.CharField(
        max_length=7,
        default='#3498db',
        help_text="Stage color (hex code for visual board)"
    )

    icon = models.CharField(
        max_length=50,
        default='fas fa-circle',
        help_text="FontAwesome icon class"
    )

    # Capacity and constraints
    capacity_limit = models.IntegerField(
        null=True,
        blank=True,
        help_text="Max bits allowed in this stage (null = unlimited)"
    )

    warn_threshold = models.IntegerField(
        null=True,
        blank=True,
        help_text="Warn when count exceeds this (bottleneck detection)"
    )

    average_duration_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected average time in this stage (for forecasting)"
    )

    # Business rules
    auto_advance_conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Conditions to auto-advance to next stage.
        Example: {"evaluation_complete": true, "quotation_approved": true}
        """
    )

    requires_assignment = models.BooleanField(
        default=False,
        help_text="Must assign to user/team before entering this stage"
    )

    requires_approval = models.BooleanField(
        default=False,
        help_text="Requires approval to exit this stage"
    )

    # Stage transitions
    allowed_next_stages = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='allowed_previous_stages',
        help_text="Stages that can follow this one"
    )

    # Flags
    is_active = models.BooleanField(
        default=True,
        help_text="Stage is active and shown on board"
    )

    is_terminal = models.BooleanField(
        default=False,
        help_text="Terminal stage (no further progression)"
    )

    class Meta:
        db_table = "planning_workflow_stage"
        verbose_name = "Workflow Stage"
        verbose_name_plural = "Workflow Stages"
        ordering = ['display_order']
        indexes = [
            models.Index(fields=['stage_code'], name='ix_ws_code'),
            models.Index(fields=['display_order'], name='ix_ws_order'),
        ]

    def __str__(self):
        return f"{self.stage_name} ({self.stage_code})"

    def get_current_count(self):
        """Get count of bits currently in this stage."""
        return self.bit_positions.filter(is_current=True).count()

    def is_at_capacity(self):
        """Check if stage is at or over capacity limit."""
        if not self.capacity_limit:
            return False
        return self.get_current_count() >= self.capacity_limit

    def is_bottleneck(self):
        """Check if stage is a bottleneck (exceeds warning threshold)."""
        if not self.warn_threshold:
            return False
        return self.get_current_count() >= self.warn_threshold

    def can_accept_bit(self):
        """Check if stage can accept another bit."""
        if not self.is_active:
            return False
        if self.capacity_limit and self.is_at_capacity():
            return False
        return True

    def get_utilization_percentage(self):
        """Get utilization as percentage of capacity."""
        if not self.capacity_limit:
            return None
        current = self.get_current_count()
        return round((current / self.capacity_limit) * 100, 1)


class BitWorkflowPosition(AuditMixin):
    """
    Tracks a drill bit's position in the visual workflow.

    Each time a bit moves to a new stage, a new record is created
    with is_current=True and the previous record is marked is_current=False.

    This provides:
    - Current position for visual board
    - Full movement history
    - Time-in-stage analytics
    - Bottleneck identification
    """

    # What bit
    job_card = models.ForeignKey(
        'production.JobCard',
        on_delete=models.CASCADE,
        related_name='workflow_positions',
        help_text="Job card being tracked"
    )

    serial_unit = models.ForeignKey(
        'inventory.SerialUnit',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='workflow_positions',
        help_text="Serial unit (if known)"
    )

    # Where it is
    stage = models.ForeignKey(
        WorkflowStage,
        on_delete=models.PROTECT,
        related_name='bit_positions',
        help_text="Current or historical stage"
    )

    # When it got here
    entered_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When bit entered this stage"
    )

    exited_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When bit exited this stage"
    )

    # Current position flag
    is_current = models.BooleanField(
        default=True,
        db_index=True,
        help_text="True if bit is currently in this stage"
    )

    # Who moved it
    moved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_moves',
        help_text="User who moved bit to this stage"
    )

    # Assignment
    assigned_to = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bits',
        help_text="User assigned to work on this bit in this stage"
    )

    # Visual position on board
    board_column = models.IntegerField(
        null=True,
        blank=True,
        help_text="Column position on kanban board (for persistence)"
    )

    board_row = models.IntegerField(
        null=True,
        blank=True,
        help_text="Row position on kanban board (for persistence)"
    )

    # Metadata
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes about this stage transition"
    )

    hold_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason if bit is on hold in this stage"
    )

    expected_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Expected completion time for this stage"
    )

    # Flags
    is_on_hold = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Bit is on hold in this stage"
    )

    is_priority = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Priority/expedite flag"
    )

    class Meta:
        db_table = "planning_bit_workflow_position"
        verbose_name = "Bit Workflow Position"
        verbose_name_plural = "Bit Workflow Positions"
        ordering = ['-entered_at']
        indexes = [
            models.Index(fields=['job_card', 'is_current'], name='ix_bwp_jc_current'),
            models.Index(fields=['stage', 'is_current'], name='ix_bwp_stage_current'),
            models.Index(fields=['entered_at'], name='ix_bwp_entered'),
            models.Index(fields=['assigned_to'], name='ix_bwp_assigned'),
            models.Index(fields=['is_priority'], name='ix_bwp_priority'),
        ]

    def __str__(self):
        status = "CURRENT" if self.is_current else "PAST"
        return f"{self.job_card.job_card_number} @ {self.stage.stage_code} ({status})"

    @property
    def time_in_stage(self):
        """
        Calculate time spent in this stage.
        Returns timedelta.
        """
        if self.is_current:
            return timezone.now() - self.entered_at
        else:
            if self.exited_at:
                return self.exited_at - self.entered_at
            return None

    @property
    def time_in_stage_hours(self):
        """Time in stage as decimal hours."""
        delta = self.time_in_stage
        if delta:
            return round(delta.total_seconds() / 3600, 2)
        return None

    @property
    def is_overdue(self):
        """Check if bit has exceeded expected duration."""
        if not self.is_current or not self.expected_completion:
            return False
        return timezone.now() > self.expected_completion

    @property
    def is_exceeding_average(self):
        """Check if time in stage exceeds average for this stage."""
        if not self.is_current or not self.stage.average_duration_hours:
            return False

        hours_in_stage = self.time_in_stage_hours
        if hours_in_stage:
            return hours_in_stage > float(self.stage.average_duration_hours)
        return False

    def move_to_stage(self, new_stage, user=None, notes='', assigned_to=None):
        """
        Move bit to a new stage.

        Creates new BitWorkflowPosition record and marks current as not current.
        Returns the new position record.
        """
        # Validate transition
        allowed = self.stage.allowed_next_stages.filter(id=new_stage.id).exists()
        if not allowed and not self.stage.allowed_next_stages.count() == 0:
            # If no allowed_next_stages defined, allow all
            raise ValueError(
                f"Cannot move from {self.stage.stage_code} to {new_stage.stage_code}: "
                f"transition not allowed"
            )

        # Check new stage capacity
        if not new_stage.can_accept_bit():
            raise ValueError(
                f"Stage {new_stage.stage_code} is at capacity "
                f"({new_stage.get_current_count()}/{new_stage.capacity_limit})"
            )

        # Mark current position as exited
        self.is_current = False
        self.exited_at = timezone.now()
        self.save(update_fields=['is_current', 'exited_at', 'updated_at'])

        # Calculate expected completion
        expected = None
        if new_stage.average_duration_hours:
            from datetime import timedelta
            expected = timezone.now() + timedelta(hours=float(new_stage.average_duration_hours))

        # Create new position
        new_position = BitWorkflowPosition.objects.create(
            job_card=self.job_card,
            serial_unit=self.serial_unit,
            stage=new_stage,
            entered_at=timezone.now(),
            is_current=True,
            moved_by=user,
            assigned_to=assigned_to,
            notes=notes,
            expected_completion=expected,
            is_priority=self.is_priority,  # Carry over priority flag
        )

        return new_position

    def put_on_hold(self, reason, user=None):
        """Put bit on hold in current stage."""
        self.is_on_hold = True
        self.hold_reason = reason
        self.save(update_fields=['is_on_hold', 'hold_reason', 'updated_at'])

    def release_from_hold(self, user=None):
        """Release bit from hold."""
        self.is_on_hold = False
        self.hold_reason = ""
        self.save(update_fields=['is_on_hold', 'hold_reason', 'updated_at'])

    def assign_to(self, user):
        """Assign bit to user."""
        self.assigned_to = user
        self.save(update_fields=['assigned_to', 'updated_at'])

    def mark_priority(self, is_priority=True):
        """Mark/unmark as priority."""
        self.is_priority = is_priority
        self.save(update_fields=['is_priority', 'updated_at'])


class VisualBoardLayout(SoftDeleteMixin, AuditMixin):
    """
    Saved board layouts/views for different users or teams.

    Users can create custom views:
    - My Assigned Bits
    - ENO Customer Jobs
    - Priority Rush Jobs
    - Bits Over 7 Days in System
    - etc.
    """

    # Owner
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='board_layouts',
        help_text="User who created this layout"
    )

    # Identification
    layout_name = models.CharField(
        max_length=100,
        help_text="Name for this board view"
    )

    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of this view"
    )

    # Filters
    filter_rules = models.JSONField(
        default=dict,
        help_text="""
        Filter criteria for bits shown on this board.
        Example:
        {
            "job_types": ["REPAIR", "RETROFIT"],
            "customers": ["ENO", "LSTK"],
            "priority_only": true,
            "assigned_to_me": true,
            "max_age_days": 7,
            "stages": ["EVAL_QUEUE", "EVALUATING", "REPAIR_QUEUE"]
        }
        """
    )

    # Display settings
    display_settings = models.JSONField(
        default=dict,
        help_text="""
        Visual display settings.
        Example:
        {
            "group_by": "customer",
            "sort_by": "entered_at",
            "show_age": true,
            "show_assignment": true,
            "compact_mode": false,
            "color_by": "priority"
        }
        """
    )

    # Stages to show
    visible_stages = models.ManyToManyField(
        WorkflowStage,
        blank=True,
        related_name='visible_in_layouts',
        help_text="Stages shown on this board (empty = all active stages)"
    )

    # Sharing
    is_shared = models.BooleanField(
        default=False,
        help_text="Shared with team/public"
    )

    shared_with_users = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='shared_board_layouts',
        help_text="Users who can see this layout"
    )

    # Default
    is_default = models.BooleanField(
        default=False,
        help_text="Default board for this user"
    )

    class Meta:
        db_table = "planning_visual_board_layout"
        verbose_name = "Visual Board Layout"
        verbose_name_plural = "Visual Board Layouts"
        ordering = ['created_by', 'layout_name']
        unique_together = ['created_by', 'layout_name']

    def __str__(self):
        return f"{self.layout_name} ({self.created_by.username})"

    def get_filtered_positions(self):
        """
        Get BitWorkflowPosition queryset based on filter_rules.
        """
        positions = BitWorkflowPosition.objects.filter(is_current=True).select_related(
            'job_card',
            'serial_unit',
            'stage',
            'assigned_to'
        )

        rules = self.filter_rules

        # Filter by job types
        if rules.get('job_types'):
            positions = positions.filter(job_card__job_type__in=rules['job_types'])

        # Filter by customers
        if rules.get('customers'):
            positions = positions.filter(job_card__customer_name__in=rules['customers'])

        # Filter by priority
        if rules.get('priority_only'):
            positions = positions.filter(is_priority=True)

        # Filter by assigned to me
        if rules.get('assigned_to_me'):
            positions = positions.filter(assigned_to=self.created_by)

        # Filter by age
        if rules.get('max_age_days'):
            from datetime import timedelta
            cutoff = timezone.now() - timedelta(days=rules['max_age_days'])
            positions = positions.filter(entered_at__gte=cutoff)

        # Filter by stages
        if rules.get('stages'):
            positions = positions.filter(stage__stage_code__in=rules['stages'])

        # Filter by on hold
        if rules.get('exclude_on_hold'):
            positions = positions.filter(is_on_hold=False)

        return positions


class WIPDashboardMetrics(models.Model):
    """
    Snapshot of WIP metrics for analytics and trending.

    Generated periodically (hourly/daily) to track:
    - Total WIP count over time
    - Stage utilization over time
    - Bottleneck trends
    - Throughput metrics
    """

    # When
    snapshot_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When this snapshot was taken"
    )

    # Overall metrics
    total_wip = models.IntegerField(
        help_text="Total bits in work (all stages except terminal)"
    )

    total_on_hold = models.IntegerField(
        default=0,
        help_text="Bits on hold"
    )

    total_priority = models.IntegerField(
        default=0,
        help_text="Priority bits"
    )

    # Stage breakdown
    stage_counts = models.JSONField(
        default=dict,
        help_text="""
        Count by stage.
        Example: {"EVAL_QUEUE": 15, "EVALUATING": 8, "REPAIR_QUEUE": 22, ...}
        """
    )

    # Bottlenecks
    bottleneck_stages = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="Stages exceeding warning threshold"
    )

    # Average age by stage
    average_age_by_stage = models.JSONField(
        default=dict,
        help_text="""
        Average hours in each stage.
        Example: {"EVAL_QUEUE": 24.5, "EVALUATING": 8.2, ...}
        """
    )

    # Throughput (bits/day)
    completed_since_last = models.IntegerField(
        default=0,
        help_text="Bits completed since last snapshot"
    )

    new_since_last = models.IntegerField(
        default=0,
        help_text="Bits added since last snapshot"
    )

    class Meta:
        db_table = "planning_wip_dashboard_metrics"
        verbose_name = "WIP Dashboard Metrics"
        verbose_name_plural = "WIP Dashboard Metrics"
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['snapshot_date'], name='ix_wdm_snapshot'),
        ]

    def __str__(self):
        return f"WIP Metrics {self.snapshot_date.strftime('%Y-%m-%d %H:%M')} - {self.total_wip} bits"

    @classmethod
    def capture_snapshot(cls):
        """
        Capture current WIP metrics.
        Call this from scheduled task (celery/cron).
        """
        from django.db.models import Avg

        # Get all current positions
        current_positions = BitWorkflowPosition.objects.filter(is_current=True)

        # Total counts
        total_wip = current_positions.count()
        total_on_hold = current_positions.filter(is_on_hold=True).count()
        total_priority = current_positions.filter(is_priority=True).count()

        # Stage counts
        stage_counts = {}
        for stage in WorkflowStage.objects.filter(is_active=True):
            stage_counts[stage.stage_code] = current_positions.filter(stage=stage).count()

        # Bottlenecks
        bottleneck_stages = []
        for stage in WorkflowStage.objects.filter(is_active=True):
            if stage.is_bottleneck():
                bottleneck_stages.append(stage.stage_code)

        # Average age by stage
        average_age_by_stage = {}
        for stage in WorkflowStage.objects.filter(is_active=True):
            stage_positions = current_positions.filter(stage=stage)
            if stage_positions.exists():
                # Calculate average hours in stage
                total_hours = sum([
                    (pos.time_in_stage_hours or 0) for pos in stage_positions
                ])
                avg_hours = round(total_hours / stage_positions.count(), 2)
                average_age_by_stage[stage.stage_code] = avg_hours

        # Throughput (compare to last snapshot)
        last_snapshot = cls.objects.order_by('-snapshot_date').first()
        completed_since_last = 0
        new_since_last = 0

        if last_snapshot:
            # Bits completed = positions that exited since last snapshot
            completed_since_last = BitWorkflowPosition.objects.filter(
                is_current=False,
                exited_at__gt=last_snapshot.snapshot_date,
                stage__is_terminal=True
            ).count()

            # New bits = positions created since last snapshot
            new_since_last = BitWorkflowPosition.objects.filter(
                entered_at__gt=last_snapshot.snapshot_date,
                stage__display_order=10  # First stage
            ).count()

        # Create snapshot
        snapshot = cls.objects.create(
            snapshot_date=timezone.now(),
            total_wip=total_wip,
            total_on_hold=total_on_hold,
            total_priority=total_priority,
            stage_counts=stage_counts,
            bottleneck_stages=bottleneck_stages,
            average_age_by_stage=average_age_by_stage,
            completed_since_last=completed_since_last,
            new_since_last=new_since_last,
        )

        return snapshot
