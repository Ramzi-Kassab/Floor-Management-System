"""
Parts and Consumables Usage Models

Track spare parts and materials used in maintenance work orders.
"""
from django.db import models
from django.conf import settings
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin
from .corrective import WorkOrder


class PartsUsage(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Tracks spare parts and consumables used in maintenance.
    Integrates with Inventory module for stock management.
    """

    TRANSACTION_TYPE_CHOICES = (
        ('USED', 'Used/Consumed'),
        ('RETURNED', 'Returned to Stock'),
        ('DAMAGED', 'Damaged During Work'),
    )

    # Work order this usage is for
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='parts_used',
        help_text="Work order that used these parts"
    )

    # Inventory reference (flexible - uses IDs for loose coupling)
    item_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to inventory.Item ID"
    )
    item_sku = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Item SKU (denormalized for display)"
    )
    item_name = models.CharField(
        max_length=200,
        help_text="Item name/description"
    )

    # Usage details
    quantity_used = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Quantity used"
    )
    unit_of_measure = models.CharField(
        max_length=50,
        default='EA',
        help_text="Unit of measure (EA, L, KG, M, etc.)"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='USED',
        help_text="Type of transaction"
    )

    # Source location
    location_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to inventory.Location ID"
    )
    location_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Location code (denormalized)"
    )

    # Cost tracking
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Cost per unit"
    )
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total cost (qty * unit cost)"
    )

    # Inventory transaction reference
    inventory_transaction_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to inventory transaction created"
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes about this part usage"
    )

    # Tracking
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parts_usage_recorded',
        help_text="Who recorded this usage"
    )
    usage_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When this usage was recorded"
    )

    class Meta:
        db_table = "maintenance_parts_usage"
        verbose_name = "Parts Usage"
        verbose_name_plural = "Parts Usage Records"
        ordering = ['-usage_date']
        indexes = [
            models.Index(fields=['work_order'], name='ix_maint_parts_wo'),
            models.Index(fields=['item_id'], name='ix_maint_parts_item'),
            models.Index(fields=['usage_date'], name='ix_maint_parts_date'),
        ]

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.item_name} ({self.quantity_used} {self.unit_of_measure})"

    def save(self, *args, **kwargs):
        # Auto-calculate total cost
        self.total_cost = self.quantity_used * self.unit_cost
        super().save(*args, **kwargs)

        # Update work order's parts cost
        self._update_wo_parts_cost()

    def _update_wo_parts_cost(self):
        """Update the work order's total parts cost."""
        from django.db.models import Sum
        total = self.work_order.parts_used.filter(
            is_deleted=False,
            transaction_type='USED'
        ).aggregate(total=Sum('total_cost'))['total'] or 0

        self.work_order.parts_cost = total
        self.work_order.save(update_fields=['parts_cost', 'updated_at'])

    @property
    def cost_display(self):
        """Formatted cost display."""
        return f"{self.total_cost:,.2f}"
