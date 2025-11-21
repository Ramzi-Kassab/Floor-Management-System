"""
NCR Financial Impact Model

Tracks financial impacts of Nonconformance Reports.
Separated from Quality module to maintain proper domain boundaries.
"""
from django.db import models
from floor_app.mixins import AuditMixin


class NCRFinancialImpact(AuditMixin):
    """
    Financial impact tracking for Nonconformance Reports.

    This model stores cost-related data for NCRs, maintaining separation
    between Quality (process/compliance) and Finance (cost/impact) domains.

    Relationship: One-to-One with quality.NonconformanceReport
    """

    # Reference to NCR (loose coupling using BigIntegerField + unique ncr_number)
    ncr_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="NCR number reference (e.g., NCR-2025-0001)"
    )

    # Financial impact fields (migrated from NonconformanceReport)
    estimated_cost_impact = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Estimated cost of the nonconformance"
    )
    actual_cost_impact = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Actual cost after resolution"
    )
    lost_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Lost revenue due to this NCR"
    )

    # Additional notes for financial context
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Financial impact notes and breakdown"
    )

    class Meta:
        db_table = "finance_ncr_financial_impact"
        verbose_name = "NCR Financial Impact"
        verbose_name_plural = "NCR Financial Impacts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ncr_number'], name='ix_fin_ncr_number'),
            models.Index(fields=['created_at'], name='ix_fin_ncr_created'),
        ]

    def __str__(self):
        return f"Financial Impact: {self.ncr_number}"

    @property
    def total_financial_impact(self):
        """Calculate total financial impact."""
        return self.actual_cost_impact + self.lost_revenue

    @property
    def cost_variance(self):
        """Calculate variance between estimated and actual cost."""
        return self.actual_cost_impact - self.estimated_cost_impact

    @property
    def has_financial_impact(self):
        """Check if there is any financial impact recorded."""
        return (
            self.estimated_cost_impact > 0 or
            self.actual_cost_impact > 0 or
            self.lost_revenue > 0
        )
