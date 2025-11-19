"""
Inventory Transaction Layer - Movement and Change Logging

Every stock movement or status change is recorded here for:
- Audit trail
- Cost tracking
- Analytics and reporting
- Future integration with Batch and JobCard systems
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import PostingMixin


class InventoryTransaction(PostingMixin):
    """
    Log of all inventory movements and state changes.

    Transaction types:
    - RECEIPT: Stock received from purchase or production
    - ISSUE: Stock issued for use (job, customer, etc.)
    - TRANSFER: Stock moved between locations
    - ADJUSTMENT: Quantity correction (count, damage, etc.)
    - SCRAP: Stock disposed as scrap
    - CONDITION_CHANGE: Condition upgrade/downgrade (e.g., NEW -> RECLAIM_AS_NEW)
    - OWNERSHIP_CHANGE: Ownership transfer (e.g., ARDT -> CUSTOMER_X)
    - RESERVE: Stock reserved for future use
    - UNRESERVE: Reserved stock released
    - RETROFIT: Bit retrofitted (MAT changed)
    """

    TRANSACTION_TYPE_CHOICES = (
        ('RECEIPT', 'Receipt'),
        ('ISSUE', 'Issue'),
        ('TRANSFER', 'Transfer'),
        ('ADJUSTMENT', 'Adjustment'),
        ('SCRAP', 'Scrap/Disposal'),
        ('CONDITION_CHANGE', 'Condition Change'),
        ('OWNERSHIP_CHANGE', 'Ownership Transfer'),
        ('RESERVE', 'Reserve Stock'),
        ('UNRESERVE', 'Unreserve Stock'),
        ('RETROFIT', 'Retrofit'),
        ('PRODUCTION', 'Production Output'),
        ('CONSUMPTION', 'Production Consumption'),
        ('RETURN', 'Return to Stock'),
        ('RECLASSIFICATION', 'Reclassification'),
    )

    # Core identification
    transaction_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="System-generated transaction number"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        db_index=True,
        help_text="Type of inventory transaction"
    )
    transaction_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Date/time of transaction"
    )

    # What moved (at least one must be set)
    item = models.ForeignKey(
        'Item',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Item for non-serialized transactions"
    )
    serial_unit = models.ForeignKey(
        'SerialUnit',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Serial unit for serialized transactions"
    )

    # Quantity moved
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Quantity changed (positive for increase, negative for decrease)"
    )
    uom = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Unit of measure"
    )

    # From/To dimensions (nullable based on transaction type)
    from_location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_out',
        help_text="Source location"
    )
    to_location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_in',
        help_text="Destination location"
    )

    from_condition = models.ForeignKey(
        'ConditionType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_from',
        help_text="Source condition"
    )
    to_condition = models.ForeignKey(
        'ConditionType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_to',
        help_text="Destination condition"
    )

    from_ownership = models.ForeignKey(
        'OwnershipType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_from',
        help_text="Source ownership (generic)"
    )
    to_ownership = models.ForeignKey(
        'OwnershipType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_to',
        help_text="Destination ownership (generic)"
    )

    # Cutter-specific ownership tracking (for Excel integration)
    # These provide finer-grained tracking than generic ownership
    # Used for cutters: ENO As New, ENO Ground, ARDT Reclaim, LSTK Reclaim, New Stock
    cutter_ownership_category = models.ForeignKey(
        'CutterOwnershipCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        help_text="Cutter ownership category (for cutter items only)"
    )

    # For transactions that affect quantity IN/OUT per ownership category
    # quantity_in: Positive quantity added to this ownership category (PO receipt, reclaim, grinding)
    # quantity_out: Positive quantity removed from this ownership category (consumption, scrap)
    quantity_in = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Quantity added to ownership category (for cutters)"
    )
    quantity_out = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Quantity removed from ownership category (for cutters)"
    )

    # For RETROFIT: MAT change tracking
    from_mat = models.ForeignKey(
        'BitDesignRevision',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_from_mat',
        help_text="Source MAT (for retrofit)"
    )
    to_mat = models.ForeignKey(
        'BitDesignRevision',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_to_mat',
        help_text="Target MAT (for retrofit)"
    )

    # Reference documents
    reference_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="Type of reference document (PO, WO, JOB_CARD, INVOICE, etc.)"
    )
    reference_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        db_index=True,
        help_text="Reference document ID/number"
    )

    # Future integration hooks (placeholder FKs)
    # These will be updated when Batch/JobCard models are implemented
    batch_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Batch ID (for future batch system integration)"
    )
    job_card_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Job Card ID (for future job card system integration)"
    )
    work_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Work Order ID (for future WO system integration)"
    )

    # Cost tracking
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Cost per unit at time of transaction"
    )
    total_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Total transaction cost"
    )
    currency = models.CharField(
        max_length=3,
        default='SAR',
        help_text="Currency code"
    )

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_transactions',
        help_text="User who created this transaction"
    )
    reason_code = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Reason code for the transaction"
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes/comments"
    )

    # Status
    is_reversed = models.BooleanField(
        default=False,
        help_text="True if this transaction was reversed"
    )
    reversed_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reverses',
        help_text="Transaction that reversed this one"
    )

    class Meta:
        db_table = "inventory_transaction"
        verbose_name = "Inventory Transaction"
        verbose_name_plural = "Inventory Transactions"
        ordering = ['-transaction_date', '-id']
        indexes = [
            models.Index(fields=['transaction_number'], name='ix_it_txn_number'),
            models.Index(fields=['transaction_date'], name='ix_it_txn_date'),
            models.Index(fields=['item'], name='ix_it_item'),
            models.Index(fields=['serial_unit'], name='ix_it_serial'),
            models.Index(fields=['transaction_type'], name='ix_it_type'),
            models.Index(fields=['reference_type', 'reference_id'], name='ix_it_reference'),
            models.Index(fields=['batch_id'], name='ix_it_batch'),
            models.Index(fields=['job_card_id'], name='ix_it_job_card'),
        ]

    def __str__(self):
        item_ref = self.serial_unit.serial_number if self.serial_unit else (self.item.sku if self.item else "?")
        return f"{self.transaction_number} | {self.transaction_type} | {item_ref} | {self.quantity}"

    @classmethod
    def generate_transaction_number(cls):
        """Generate a unique transaction number."""
        from datetime import datetime
        prefix = datetime.now().strftime("TXN%Y%m%d")
        last = cls.objects.filter(
            transaction_number__startswith=prefix
        ).order_by('-transaction_number').first()

        if last:
            last_seq = int(last.transaction_number[-6:])
            new_seq = last_seq + 1
        else:
            new_seq = 1

        return f"{prefix}{new_seq:06d}"

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = self.generate_transaction_number()

        # Auto-calculate total cost if not set
        if not self.total_cost and self.unit_cost and self.quantity:
            self.total_cost = abs(self.quantity) * self.unit_cost

        super().save(*args, **kwargs)

    @property
    def is_movement(self):
        """Check if this is a physical movement transaction."""
        return self.transaction_type in ('TRANSFER', 'RECEIPT', 'ISSUE', 'RETURN')

    @property
    def is_state_change(self):
        """Check if this is a state/attribute change transaction."""
        return self.transaction_type in (
            'CONDITION_CHANGE', 'OWNERSHIP_CHANGE', 'RETROFIT', 'RECLASSIFICATION'
        )

    @property
    def is_quantity_change(self):
        """Check if this affects stock quantities."""
        return self.transaction_type in (
            'RECEIPT', 'ISSUE', 'ADJUSTMENT', 'SCRAP', 'PRODUCTION', 'CONSUMPTION', 'RETURN'
        )

    def create_reversal(self, user=None, reason='Reversal'):
        """
        Create a reversal transaction for this transaction.

        Returns the reversal transaction.
        """
        if self.is_reversed:
            raise ValueError("Transaction is already reversed")

        reversal = InventoryTransaction.objects.create(
            transaction_type=self.transaction_type,
            item=self.item,
            serial_unit=self.serial_unit,
            quantity=-self.quantity,  # Opposite quantity
            uom=self.uom,
            # Swap from/to
            from_location=self.to_location,
            to_location=self.from_location,
            from_condition=self.to_condition,
            to_condition=self.from_condition,
            from_ownership=self.to_ownership,
            to_ownership=self.from_ownership,
            from_mat=self.to_mat,
            to_mat=self.from_mat,
            reference_type='REVERSAL',
            reference_id=self.transaction_number,
            unit_cost=self.unit_cost,
            total_cost=-self.total_cost if self.total_cost else None,
            created_by=user,
            reason_code='REVERSAL',
            notes=f"{reason}. Original: {self.transaction_number}"
        )

        # Mark original as reversed
        self.is_reversed = True
        self.reversed_by = reversal
        self.save(update_fields=['is_reversed', 'reversed_by'])

        return reversal
