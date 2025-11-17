"""
Downtime tracking and production impact models.
"""
from django.db import models
from django.conf import settings
from floor_app.mixins import AuditMixin, SoftDeleteMixin


class DowntimeEvent(AuditMixin, SoftDeleteMixin, models.Model):
    """Track downtime/stoppage events for assets."""

    class EventType(models.TextChoices):
        UNPLANNED_BREAKDOWN = 'UNPLANNED_BREAKDOWN', 'Unplanned Breakdown'
        PLANNED_PM = 'PLANNED_PM', 'Planned PM'
        SETUP_CHANGEOVER = 'SETUP_CHANGEOVER', 'Setup/Changeover'
        WAITING_PARTS = 'WAITING_PARTS', 'Waiting for Parts'
        UTILITY_FAILURE = 'UTILITY_FAILURE', 'Utility Failure (Power/Air)'
        OPERATOR_ABSENCE = 'OPERATOR_ABSENCE', 'Operator Absence'
        QUALITY_ISSUE = 'QUALITY_ISSUE', 'Quality Hold'
        OTHER = 'OTHER', 'Other'

    class Severity(models.TextChoices):
        MINOR = 'MINOR', 'Minor (< 1 hour)'
        MODERATE = 'MODERATE', 'Moderate (1-4 hours)'
        MAJOR = 'MAJOR', 'Major (4-8 hours)'
        CRITICAL = 'CRITICAL', 'Critical (> 8 hours)'

    class ReasonCategory(models.TextChoices):
        MECHANICAL = 'MECHANICAL', 'Mechanical'
        ELECTRICAL = 'ELECTRICAL', 'Electrical'
        HYDRAULIC = 'HYDRAULIC', 'Hydraulic'
        PNEUMATIC = 'PNEUMATIC', 'Pneumatic'
        CONTROL_SOFTWARE = 'CONTROL_SOFTWARE', 'Control/Software'
        WEAR = 'WEAR', 'Wear & Tear'
        MISUSE = 'MISUSE', 'Operator Error'
        UTILITY = 'UTILITY', 'Utility Issue'
        MATERIAL = 'MATERIAL', 'Material Issue'
        TOOLING = 'TOOLING', 'Tooling Issue'
        OTHER = 'OTHER', 'Other'

    asset = models.ForeignKey(
        'maintenance.Asset', on_delete=models.PROTECT, related_name='downtime_events'
    )
    work_order = models.ForeignKey(
        'maintenance.MaintenanceWorkOrder', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='downtime_events'
    )

    event_type = models.CharField(max_length=30, choices=EventType.choices)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    is_planned = models.BooleanField(default=False)
    reason_category = models.CharField(max_length=20, choices=ReasonCategory.choices, blank=True)
    reason_description = models.TextField(blank=True)

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MODERATE)
    notes = models.TextField(blank=True)

    # Financial impact flag
    has_production_impact = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Downtime Event'
        verbose_name_plural = 'Downtime Events'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['asset', 'start_time']),
            models.Index(fields=['event_type', 'start_time']),
            models.Index(fields=['is_planned']),
            models.Index(fields=['has_production_impact']),
        ]
        permissions = [
            ('can_record_downtime', 'Can record downtime events'),
        ]

    def __str__(self):
        return f"{self.asset.asset_code} - {self.get_event_type_display()} @ {self.start_time}"

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)

    @property
    def duration_hours(self):
        if self.duration_minutes:
            return round(self.duration_minutes / 60, 2)
        return 0

    @property
    def is_ongoing(self):
        return self.end_time is None

    def close_event(self, end_time=None):
        from django.utils import timezone
        self.end_time = end_time or timezone.now()
        delta = self.end_time - self.start_time
        self.duration_minutes = int(delta.total_seconds() / 60)
        # Auto-set severity based on duration
        if self.duration_minutes < 60:
            self.severity = self.Severity.MINOR
        elif self.duration_minutes < 240:
            self.severity = self.Severity.MODERATE
        elif self.duration_minutes < 480:
            self.severity = self.Severity.MAJOR
        else:
            self.severity = self.Severity.CRITICAL
        self.save()


class ProductionImpact(AuditMixin, models.Model):
    """Links downtime to production batches/jobs and tracks financial impact."""

    class ImpactType(models.TextChoices):
        BATCH = 'BATCH', 'Batch/Order'
        JOB_CARD = 'JOB_CARD', 'Individual Job Card'
        OPERATION = 'OPERATION', 'Specific Operation'

    downtime_event = models.ForeignKey(
        DowntimeEvent, on_delete=models.CASCADE, related_name='production_impacts'
    )

    impact_type = models.CharField(max_length=20, choices=ImpactType.choices, default=ImpactType.BATCH)

    # Future production module FKs (nullable for now)
    batch_id = models.PositiveBigIntegerField(null=True, blank=True, help_text="FK to Batch when available")
    job_card_id = models.PositiveBigIntegerField(null=True, blank=True, help_text="FK to JobCard when available")
    operation_id = models.PositiveBigIntegerField(null=True, blank=True, help_text="FK to Operation when available")

    # Text references for now
    batch_reference = models.CharField(max_length=100, blank=True)
    job_card_number = models.CharField(max_length=100, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    product_description = models.CharField(max_length=255, blank=True)

    # Timing impact
    expected_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    delay_minutes = models.PositiveIntegerField(null=True, blank=True)

    # Financial impact
    lost_or_delayed_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default='SAR')
    is_revenue_confirmed = models.BooleanField(default=False)

    impact_description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Production Impact'
        verbose_name_plural = 'Production Impacts'
        ordering = ['-created_at']

    def __str__(self):
        ref = self.batch_reference or self.job_card_number or 'Unknown'
        return f"{self.downtime_event.asset.asset_code} impact on {ref}"

    @property
    def delay_hours(self):
        if self.delay_minutes:
            return round(self.delay_minutes / 60, 2)
        return 0


class LostSalesRecord(AuditMixin, models.Model):
    """Confirmed financial impact from downtime."""

    production_impact = models.OneToOneField(
        ProductionImpact, on_delete=models.CASCADE, related_name='lost_sales_record'
    )

    customer_name = models.CharField(max_length=255)
    order_reference = models.CharField(max_length=100)
    original_order_value = models.DecimalField(max_digits=12, decimal_places=2)

    revenue_lost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revenue_delayed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recovery_possible = models.BooleanField(default=True, help_text="Can revenue be recovered later?")

    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Lost Sales Record'
        verbose_name_plural = 'Lost Sales Records'
        ordering = ['-confirmed_at']
        permissions = [
            ('can_confirm_lost_sales', 'Can confirm lost sales records'),
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.order_reference}: {self.revenue_lost}"

    @property
    def total_impact(self):
        return self.revenue_lost + self.revenue_delayed
