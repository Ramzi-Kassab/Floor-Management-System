"""
Downtime and Production Impact Models

Models for tracking equipment downtime and its impact on production and revenue.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin
from .asset import Asset
from .corrective import WorkOrder


class DowntimeEvent(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Records of asset downtime - when equipment was not available.
    Tracks both planned and unplanned downtime.
    """

    DOWNTIME_TYPE_CHOICES = (
        ('PLANNED', 'Planned (PM/Setup)'),
        ('UNPLANNED', 'Unplanned (Breakdown)'),
    )

    REASON_CATEGORY_CHOICES = (
        ('BREAKDOWN', 'Equipment Breakdown'),
        ('PM_SCHEDULED', 'Scheduled Preventive Maintenance'),
        ('SETUP', 'Setup/Changeover'),
        ('NO_OPERATOR', 'No Operator Available'),
        ('NO_MATERIAL', 'No Material/Input'),
        ('QUALITY_ISSUE', 'Quality Issue'),
        ('UTILITY_FAILURE', 'Utility Failure (Power/Air/Water)'),
        ('SAFETY_STOP', 'Safety Stop'),
        ('INSPECTION', 'Inspection/Testing'),
        ('OTHER', 'Other'),
    )

    # Asset that was down
    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='downtime_events',
        help_text="Asset that experienced downtime"
    )

    # Related work order (if any)
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='downtime_events',
        help_text="Associated work order"
    )

    # Timing
    start_time = models.DateTimeField(
        db_index=True,
        help_text="When downtime started"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When downtime ended (null if ongoing)"
    )
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total downtime duration in minutes"
    )

    # Classification
    downtime_type = models.CharField(
        max_length=20,
        choices=DOWNTIME_TYPE_CHOICES,
        db_index=True,
        help_text="Whether this was planned or unplanned"
    )
    reason_category = models.CharField(
        max_length=20,
        choices=REASON_CATEGORY_CHOICES,
        db_index=True,
        help_text="Primary reason for downtime"
    )
    reason_detail = models.TextField(
        blank=True,
        default="",
        help_text="Detailed explanation of the downtime reason"
    )

    # Impact assessment
    production_affected = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether production was affected"
    )
    severity_score = models.PositiveIntegerField(
        default=1,
        help_text="Severity score 1-10 (1=minimal, 10=critical)"
    )

    # Who reported/recorded
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_downtime',
        help_text="Who reported this downtime"
    )

    # Verified/confirmed
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this downtime record has been verified"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_downtime',
        help_text="Who verified this record"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When verified"
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes"
    )

    class Meta:
        db_table = "maintenance_downtime_event"
        verbose_name = "Downtime Event"
        verbose_name_plural = "Downtime Events"
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['asset', 'start_time'], name='ix_maint_dt_asset_start'),
            models.Index(fields=['downtime_type', 'reason_category'], name='ix_maint_dt_type_reason'),
            models.Index(fields=['start_time', 'end_time'], name='ix_maint_dt_times'),
            models.Index(fields=['production_affected'], name='ix_maint_dt_prod_aff'),
            models.Index(fields=['is_verified'], name='ix_maint_dt_verified'),
        ]

    def __str__(self):
        duration = self.duration_display
        return f"{self.asset.asset_code} - {self.get_reason_category_display()} ({duration})"

    def save(self, *args, **kwargs):
        # Auto-calculate duration if both times are set
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)

    @property
    def is_ongoing(self):
        """Check if downtime is still ongoing."""
        return self.end_time is None

    @property
    def duration_display(self):
        """Human-readable duration."""
        if self.is_ongoing:
            # Calculate current duration
            delta = timezone.now() - self.start_time
            minutes = int(delta.total_seconds() / 60)
        else:
            minutes = self.duration_minutes or 0

        if minutes < 60:
            return f"{minutes} min"
        hours = minutes // 60
        mins = minutes % 60
        if mins:
            return f"{hours}h {mins}m"
        return f"{hours}h"

    @property
    def duration_hours(self):
        """Duration in hours (decimal)."""
        if self.duration_minutes:
            return round(self.duration_minutes / 60, 2)
        if self.is_ongoing:
            delta = timezone.now() - self.start_time
            return round(delta.total_seconds() / 3600, 2)
        return 0

    @property
    def type_display_class(self):
        """Bootstrap class for type badge."""
        if self.downtime_type == 'PLANNED':
            return 'info'
        return 'danger'

    @property
    def severity_display_class(self):
        """Bootstrap class for severity."""
        if self.severity_score <= 3:
            return 'success'
        elif self.severity_score <= 6:
            return 'warning'
        else:
            return 'danger'

    def end_downtime(self):
        """End the downtime event."""
        self.end_time = timezone.now()
        if self.start_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        self.save(update_fields=['end_time', 'duration_minutes', 'updated_at'])

    def verify(self, user):
        """Verify the downtime record."""
        self.is_verified = True
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_by', 'verified_at', 'updated_at'])


class ProductionImpact(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Links downtime to specific production jobs/batches affected.
    Records the impact on production operations.
    """

    downtime_event = models.ForeignKey(
        DowntimeEvent,
        on_delete=models.CASCADE,
        related_name='production_impacts',
        help_text="Downtime event that caused this impact"
    )

    # Production references (using IDs for flexibility)
    batch_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to production.BatchOrder ID"
    )
    batch_order_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Batch/Order number (denormalized)"
    )
    job_card_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to production.JobCard ID"
    )
    job_card_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Job card number (denormalized)"
    )

    # Impact details
    delay_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Delay caused in minutes"
    )
    planned_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Original planned completion time"
    )
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual/revised completion time"
    )

    # Impact description
    impact_description = models.TextField(
        blank=True,
        default="",
        help_text="Description of how production was impacted"
    )

    # Quantitative impact
    units_affected = models.PositiveIntegerField(
        default=0,
        help_text="Number of units/bits affected"
    )
    rework_required = models.BooleanField(
        default=False,
        help_text="Whether rework is required"
    )
    scrap_generated = models.BooleanField(
        default=False,
        help_text="Whether scrap was generated"
    )

    class Meta:
        db_table = "maintenance_production_impact"
        verbose_name = "Production Impact"
        verbose_name_plural = "Production Impacts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['downtime_event'], name='ix_maint_pi_dt_event'),
            models.Index(fields=['batch_order_id'], name='ix_maint_pi_batch'),
            models.Index(fields=['job_card_id'], name='ix_maint_pi_job'),
        ]

    def __str__(self):
        ref = self.job_card_number or self.batch_order_number or f"Impact {self.pk}"
        return f"{ref} - {self.delay_minutes} min delay"

    @property
    def delay_display(self):
        """Human-readable delay."""
        if self.delay_minutes < 60:
            return f"{self.delay_minutes} min"
        hours = self.delay_minutes // 60
        mins = self.delay_minutes % 60
        if mins:
            return f"{hours}h {mins}m"
        return f"{hours}h"


class LostSales(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Records financial impact of downtime - lost or delayed revenue.
    Critical for tracking the business impact of maintenance issues.
    """

    IMPACT_TYPE_CHOICES = (
        ('LOST', 'Lost Sale (Order Cancelled)'),
        ('DELAYED', 'Delayed Delivery'),
        ('PENALTY', 'Late Delivery Penalty'),
        ('REWORK', 'Rework Cost'),
        ('WARRANTY', 'Warranty Claim'),
        ('REPUTATION', 'Reputation Damage'),
        ('OTHER', 'Other Financial Impact'),
    )

    CURRENCY_CHOICES = (
        ('SAR', 'Saudi Riyal'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    )

    # Link to downtime
    downtime_event = models.ForeignKey(
        DowntimeEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lost_sales',
        help_text="Related downtime event"
    )
    production_impact = models.ForeignKey(
        ProductionImpact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lost_sales',
        help_text="Related production impact"
    )

    # Reference to order/customer
    batch_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to production.BatchOrder"
    )
    batch_order_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Order number (denormalized)"
    )
    customer_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Customer name"
    )
    customer_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Customer ID reference"
    )

    # Impact classification
    impact_type = models.CharField(
        max_length=20,
        choices=IMPACT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of financial impact"
    )

    # Delivery dates
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Original expected delivery date"
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual/revised delivery date"
    )
    delay_days = models.PositiveIntegerField(
        default=0,
        help_text="Number of days delayed"
    )

    # Revenue impact
    lost_or_delayed_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Amount of lost or delayed revenue"
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='SAR',
        help_text="Currency of the amount"
    )
    is_confirmed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this is a confirmed figure or estimate"
    )

    # Recovery
    recovered_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Amount recovered (insurance, vendor penalty, etc.)"
    )

    # Notes and justification
    calculation_basis = models.TextField(
        blank=True,
        default="",
        help_text="How the amount was calculated"
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes"
    )

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_lost_sales',
        help_text="Manager who approved this estimate"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When approved"
    )

    class Meta:
        db_table = "maintenance_lost_sales"
        verbose_name = "Lost Sales Record"
        verbose_name_plural = "Lost Sales Records"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['impact_type'], name='ix_maint_ls_type'),
            models.Index(fields=['is_confirmed'], name='ix_maint_ls_confirmed'),
            models.Index(fields=['downtime_event'], name='ix_maint_ls_dt_event'),
            models.Index(fields=['batch_order_id'], name='ix_maint_ls_batch'),
        ]

    def __str__(self):
        return f"{self.get_impact_type_display()} - {self.lost_or_delayed_revenue} {self.currency}"

    @property
    def net_impact(self):
        """Net financial impact after recovery."""
        return self.lost_or_delayed_revenue - self.recovered_amount

    @property
    def impact_display_class(self):
        """Bootstrap class for impact type badge."""
        mapping = {
            'LOST': 'danger',
            'DELAYED': 'warning',
            'PENALTY': 'danger',
            'REWORK': 'warning',
            'WARRANTY': 'info',
            'REPUTATION': 'dark',
            'OTHER': 'secondary',
        }
        return mapping.get(self.impact_type, 'secondary')

    @property
    def confirmation_display_class(self):
        """Bootstrap class for confirmation status."""
        return 'success' if self.is_confirmed else 'warning'

    def approve(self, user):
        """Approve the lost sales record."""
        self.approved_by = user
        self.approved_at = timezone.now()
        self.is_confirmed = True
        self.save(update_fields=['approved_by', 'approved_at', 'is_confirmed', 'updated_at'])
