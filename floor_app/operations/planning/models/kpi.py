"""
Planning & KPI - Key Performance Indicator Management
KPI definitions and value tracking.
"""
from django.db import models
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class KPIDefinition(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Define what KPIs to track.
    Includes targets, thresholds, and calculation methods.
    """
    CATEGORY_CHOICES = [
        ('DELIVERY', 'Delivery Performance'),
        ('QUALITY', 'Quality Metrics'),
        ('EFFICIENCY', 'Efficiency/Utilization'),
        ('COST', 'Cost Metrics'),
        ('SAFETY', 'Safety Metrics'),
        ('PRODUCTIVITY', 'Productivity Metrics'),
    ]

    AGGREGATION_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="KPI code (e.g., OTD, TAT, REWORK_RATE)"
    )
    name = models.CharField(max_length=200)
    description = models.TextField()

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    unit = models.CharField(
        max_length=50,
        help_text="Unit of measurement (%, hours, count, SAR)"
    )
    calculation_method = models.TextField(
        help_text="How to calculate this KPI"
    )

    # Targets and thresholds
    target_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Target value to achieve"
    )
    warning_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Value that triggers warning"
    )
    critical_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Value that triggers critical alert"
    )

    # Direction
    higher_is_better = models.BooleanField(
        default=True,
        help_text="Is a higher value better (True) or lower (False)?"
    )

    aggregation_period = models.CharField(
        max_length=20,
        choices=AGGREGATION_CHOICES,
        default='MONTHLY'
    )
    is_active = models.BooleanField(default=True)

    # Display settings
    display_order = models.PositiveIntegerField(default=0)
    show_on_dashboard = models.BooleanField(default=True)
    decimal_places = models.PositiveIntegerField(default=2)

    class Meta:
        db_table = "planning_kpi_definition"
        verbose_name = "KPI Definition"
        verbose_name_plural = "KPI Definitions"
        ordering = ['category', 'display_order', 'code']
        indexes = [
            models.Index(fields=['code'], name='ix_plan_kpidef_code'),
            models.Index(fields=['category'], name='ix_plan_kpidef_cat'),
            models.Index(fields=['is_active'], name='ix_plan_kpidef_active'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def evaluate_value(self, value):
        """
        Evaluate a value against targets and thresholds.
        Returns: 'ON_TARGET', 'WARNING', 'CRITICAL', or 'UNKNOWN'
        """
        if value is None:
            return 'UNKNOWN'

        value = float(value)

        if self.higher_is_better:
            if self.target_value and value >= float(self.target_value):
                return 'ON_TARGET'
            if self.warning_threshold and value < float(self.warning_threshold):
                if self.critical_threshold and value < float(self.critical_threshold):
                    return 'CRITICAL'
                return 'WARNING'
            return 'WARNING'
        else:  # Lower is better
            if self.target_value and value <= float(self.target_value):
                return 'ON_TARGET'
            if self.warning_threshold and value > float(self.warning_threshold):
                if self.critical_threshold and value > float(self.critical_threshold):
                    return 'CRITICAL'
                return 'WARNING'
            return 'WARNING'


class KPIValue(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Actual KPI measurements.
    Stores calculated values for specific time periods and contexts.
    """
    kpi_definition = models.ForeignKey(
        KPIDefinition,
        on_delete=models.CASCADE,
        related_name='values'
    )

    # Time dimension
    period_start = models.DateField(db_index=True)
    period_end = models.DateField(db_index=True)

    # Value
    value = models.DecimalField(max_digits=12, decimal_places=4)

    # Context (optional - for drill-down)
    job_card_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to production.JobCard (for job-level KPIs)"
    )
    batch_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to production.BatchOrder"
    )
    customer_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Customer for customer-specific KPIs"
    )
    employee_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to hr.HREmployee (for employee performance)"
    )
    asset_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to maintenance.Asset (for equipment KPIs)"
    )
    department = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Department for department-level KPIs"
    )

    # Calculated fields
    is_on_target = models.BooleanField(default=True)
    variance_from_target = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "planning_kpi_value"
        verbose_name = "KPI Value"
        verbose_name_plural = "KPI Values"
        ordering = ['kpi_definition', '-period_start']
        indexes = [
            models.Index(
                fields=['kpi_definition', 'period_start'],
                name='ix_plan_kpival_def_start'
            ),
            models.Index(
                fields=['customer_name', 'period_start'],
                name='ix_plan_kpival_cust_start'
            ),
            models.Index(fields=['period_start'], name='ix_plan_kpival_start'),
            models.Index(fields=['is_on_target'], name='ix_plan_kpival_target'),
        ]

    def __str__(self):
        return f"{self.kpi_definition.code} - {self.period_start} to {self.period_end}: {self.value}"

    def save(self, *args, **kwargs):
        """Calculate variance from target before saving."""
        if self.kpi_definition.target_value:
            self.variance_from_target = float(self.value) - float(
                self.kpi_definition.target_value
            )

        # Evaluate if on target
        evaluation = self.kpi_definition.evaluate_value(self.value)
        self.is_on_target = evaluation == 'ON_TARGET'

        super().save(*args, **kwargs)

    @property
    def status(self):
        """Get status based on thresholds."""
        return self.kpi_definition.evaluate_value(self.value)

    @property
    def variance_percentage(self):
        """Calculate variance as percentage of target."""
        if self.kpi_definition.target_value and self.kpi_definition.target_value != 0:
            return (self.variance_from_target / float(self.kpi_definition.target_value)) * 100
        return None
