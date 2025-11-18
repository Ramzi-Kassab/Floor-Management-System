"""
Planning & KPI - Job Metrics and WIP Tracking
Per-job performance metrics, WIP snapshots, and delivery forecasting.
"""
from django.db import models
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class JobMetrics(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Per-job performance metrics.
    Aggregates various performance indicators for a single job.
    """
    job_card_id = models.BigIntegerField(
        unique=True,
        db_index=True,
        help_text="Reference to production.JobCard"
    )

    # Turnaround time breakdown
    total_turnaround_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total time from job creation to completion"
    )
    active_work_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hours of actual work performed"
    )
    waiting_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hours spent waiting (for materials, approvals, etc.)"
    )
    queue_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hours in queue between operations"
    )

    # Quality metrics
    rework_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times job required rework"
    )
    ncr_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of NCRs raised for this job"
    )
    defect_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Defect rate as percentage"
    )
    first_pass_yield = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="First pass yield percentage"
    )

    # Delivery performance
    planned_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Originally planned completion date"
    )
    actual_completion = models.DateTimeField(
        null=True,
        blank=True
    )
    is_on_time = models.BooleanField(default=True)
    delay_days = models.IntegerField(
        default=0,
        help_text="Positive = late, Negative = early"
    )

    # Cost performance
    estimated_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    actual_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    cost_variance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Positive = over budget, Negative = under budget"
    )
    labor_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    material_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # Efficiency metrics
    efficiency_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual vs standard time efficiency"
    )
    utilization_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Resource utilization percentage"
    )

    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "planning_job_metrics"
        verbose_name = "Job Metrics"
        verbose_name_plural = "Job Metrics"
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['job_card_id'], name='ix_plan_jobmet_job'),
            models.Index(fields=['is_on_time'], name='ix_plan_jobmet_ontime'),
            models.Index(
                fields=['actual_completion'],
                name='ix_plan_jobmet_complete'
            ),
        ]

    def __str__(self):
        return f"Metrics for Job #{self.job_card_id}"

    def calculate_cost_variance(self):
        """Calculate and update cost variance."""
        self.cost_variance = float(self.actual_cost) - float(self.estimated_cost)
        self.save()

    def update_delivery_status(self):
        """Update on-time status based on actual vs planned completion."""
        if self.actual_completion and self.planned_completion:
            delta = self.actual_completion - self.planned_completion
            self.delay_days = delta.days
            self.is_on_time = delta.days <= 0
            self.save()

    @property
    def cost_variance_percentage(self):
        """Calculate cost variance as percentage."""
        if self.estimated_cost and self.estimated_cost > 0:
            return (float(self.cost_variance) / float(self.estimated_cost)) * 100
        return None

    @property
    def flow_efficiency(self):
        """Calculate flow efficiency (active work / total turnaround)."""
        if self.total_turnaround_hours and self.active_work_hours:
            return (
                float(self.active_work_hours) / float(self.total_turnaround_hours)
            ) * 100
        return None


class WIPSnapshot(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Point-in-time WIP (Work In Progress) status snapshot.
    Used for trend analysis and bottleneck identification.
    """
    snapshot_time = models.DateTimeField(db_index=True)

    # Aggregate job counts
    total_jobs_in_wip = models.PositiveIntegerField(default=0)
    jobs_on_track = models.PositiveIntegerField(default=0)
    jobs_at_risk = models.PositiveIntegerField(default=0)
    jobs_delayed = models.PositiveIntegerField(default=0)

    # By status/stage
    jobs_in_evaluation = models.PositiveIntegerField(default=0)
    jobs_awaiting_approval = models.PositiveIntegerField(default=0)
    jobs_awaiting_materials = models.PositiveIntegerField(default=0)
    jobs_in_production = models.PositiveIntegerField(default=0)
    jobs_under_qc = models.PositiveIntegerField(default=0)
    jobs_on_hold = models.PositiveIntegerField(default=0)

    # Bottlenecks
    bottleneck_resources_json = models.JSONField(
        default=list,
        help_text="List of overloaded resources with utilization data"
    )

    # Value metrics
    total_wip_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total value of jobs currently in WIP"
    )

    # Age analysis
    avg_age_days = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Average age of jobs in WIP"
    )
    max_age_days = models.PositiveIntegerField(
        default=0,
        help_text="Age of oldest job in WIP"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "planning_wip_snapshot"
        verbose_name = "WIP Snapshot"
        verbose_name_plural = "WIP Snapshots"
        ordering = ['-snapshot_time']
        indexes = [
            models.Index(
                fields=['snapshot_time'],
                name='ix_plan_wipsn_time'
            ),
        ]

    def __str__(self):
        return f"WIP Snapshot - {self.snapshot_time}"

    @property
    def health_score(self):
        """Calculate overall WIP health score (0-100)."""
        if self.total_jobs_in_wip == 0:
            return 100

        on_track_pct = (self.jobs_on_track / self.total_jobs_in_wip) * 100
        delayed_penalty = (self.jobs_delayed / self.total_jobs_in_wip) * 50
        at_risk_penalty = (self.jobs_at_risk / self.total_jobs_in_wip) * 25

        score = on_track_pct - delayed_penalty - at_risk_penalty
        return max(0, min(100, score))

    def add_bottleneck(self, resource_code, utilization_pct, queue_depth):
        """Add a bottleneck resource to the list."""
        if not self.bottleneck_resources_json:
            self.bottleneck_resources_json = []

        self.bottleneck_resources_json.append({
            'resource': resource_code,
            'utilization': utilization_pct,
            'queue_depth': queue_depth,
            'timestamp': timezone.now().isoformat()
        })
        self.save()


class DeliveryForecast(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Predicted delivery dates and risk assessment.
    Helps manage customer expectations and identify at-risk jobs.
    """
    CONFIDENCE_CHOICES = [
        ('HIGH', 'High - 90%+ probability'),
        ('MEDIUM', 'Medium - 70-90% probability'),
        ('LOW', 'Low - <70% probability'),
    ]

    job_card_id = models.BigIntegerField(
        db_index=True,
        help_text="Reference to production.JobCard"
    )
    batch_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to production.BatchOrder"
    )

    # Customer commitment
    customer_required_date = models.DateField(
        help_text="Date customer expects delivery"
    )

    # Forecast
    forecast_date = models.DateField(
        help_text="Predicted completion date based on current progress"
    )
    confidence_level = models.CharField(
        max_length=20,
        choices=CONFIDENCE_CHOICES
    )

    # Risk factors
    risk_factors_json = models.JSONField(
        default=list,
        help_text="List of identified risk factors"
    )

    # Potential impact
    potential_delay_days = models.IntegerField(
        default=0,
        help_text="Estimated delay from customer required date"
    )
    at_risk = models.BooleanField(default=False)

    # Actions needed
    actions_required = models.TextField(
        blank=True,
        default="",
        help_text="Recommended actions to mitigate risk"
    )

    # Escalation
    escalation_required = models.BooleanField(default=False)
    escalation_reason = models.TextField(blank=True, default="")

    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "planning_delivery_forecast"
        verbose_name = "Delivery Forecast"
        verbose_name_plural = "Delivery Forecasts"
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['job_card_id'], name='ix_plan_delfor_job'),
            models.Index(fields=['at_risk'], name='ix_plan_delfor_risk'),
            models.Index(
                fields=['forecast_date'],
                name='ix_plan_delfor_forecast'
            ),
            models.Index(
                fields=['customer_required_date'],
                name='ix_plan_delfor_custdate'
            ),
        ]

    def __str__(self):
        return f"Forecast Job #{self.job_card_id} - {self.forecast_date}"

    def save(self, *args, **kwargs):
        """Calculate delay and risk status before saving."""
        delta = self.forecast_date - self.customer_required_date
        self.potential_delay_days = delta.days

        # Update at_risk status
        if self.potential_delay_days > 0:
            self.at_risk = True
        elif self.confidence_level == 'LOW':
            self.at_risk = True
        else:
            self.at_risk = False

        # Check if escalation needed
        if self.potential_delay_days > 7 or self.confidence_level == 'LOW':
            self.escalation_required = True

        super().save(*args, **kwargs)

    def add_risk_factor(self, factor_description, severity='MEDIUM'):
        """Add a risk factor to the list."""
        if not self.risk_factors_json:
            self.risk_factors_json = []

        self.risk_factors_json.append({
            'factor': factor_description,
            'severity': severity,
            'added_at': timezone.now().isoformat()
        })
        self.save()

    @property
    def days_until_due(self):
        """Calculate days until customer required date."""
        return (self.customer_required_date - timezone.now().date()).days

    @property
    def urgency_level(self):
        """Determine urgency based on days until due and risk."""
        days_left = self.days_until_due

        if self.at_risk and days_left <= 7:
            return 'CRITICAL'
        if self.at_risk or days_left <= 14:
            return 'HIGH'
        if days_left <= 30:
            return 'MEDIUM'
        return 'LOW'
