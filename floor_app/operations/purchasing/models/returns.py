"""
Purchase Returns Models

Handles return of goods to suppliers (RMA - Return Merchandise Authorization).
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class ReturnStatus:
    """Purchase Return status states"""
    DRAFT = 'DRAFT'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    RMA_REQUESTED = 'RMA_REQUESTED'
    RMA_APPROVED = 'RMA_APPROVED'
    READY_TO_SHIP = 'READY_TO_SHIP'
    SHIPPED = 'SHIPPED'
    RECEIVED_BY_SUPPLIER = 'RECEIVED_BY_SUPPLIER'
    CREDIT_RECEIVED = 'CREDIT_RECEIVED'
    CLOSED = 'CLOSED'
    CANCELLED = 'CANCELLED'

    CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (RMA_REQUESTED, 'RMA Requested'),
        (RMA_APPROVED, 'RMA Approved by Supplier'),
        (READY_TO_SHIP, 'Ready to Ship'),
        (SHIPPED, 'Shipped'),
        (RECEIVED_BY_SUPPLIER, 'Received by Supplier'),
        (CREDIT_RECEIVED, 'Credit Note Received'),
        (CLOSED, 'Closed'),
        (CANCELLED, 'Cancelled'),
    ]


class ReturnReason:
    """Reasons for returning goods"""
    DEFECTIVE = 'DEFECTIVE'
    WRONG_ITEM = 'WRONG_ITEM'
    WRONG_QTY = 'WRONG_QTY'
    DAMAGED = 'DAMAGED'
    QUALITY_ISSUE = 'QUALITY_ISSUE'
    NOT_AS_ORDERED = 'NOT_AS_ORDERED'
    EXPIRED = 'EXPIRED'
    DUPLICATE = 'DUPLICATE'
    OTHER = 'OTHER'

    CHOICES = [
        (DEFECTIVE, 'Defective Product'),
        (WRONG_ITEM, 'Wrong Item Shipped'),
        (WRONG_QTY, 'Wrong Quantity'),
        (DAMAGED, 'Damaged in Transit'),
        (QUALITY_ISSUE, 'Quality Does Not Meet Specs'),
        (NOT_AS_ORDERED, 'Not as Ordered'),
        (EXPIRED, 'Expired/Past Shelf Life'),
        (DUPLICATE, 'Duplicate Shipment'),
        (OTHER, 'Other'),
    ]


class ReturnAction:
    """Expected action for returned goods"""
    REPLACE = 'REPLACE'
    CREDIT = 'CREDIT'
    REPAIR = 'REPAIR'
    SCRAP = 'SCRAP'

    CHOICES = [
        (REPLACE, 'Replace with New'),
        (CREDIT, 'Credit Note'),
        (REPAIR, 'Repair and Return'),
        (SCRAP, 'Scrap (No Credit)'),
    ]


class PurchaseReturn(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Purchase Return document for returning goods to supplier.
    """
    # Identification
    return_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Auto-generated return number"
    )
    status = models.CharField(
        max_length=25,
        choices=ReturnStatus.CHOICES,
        default=ReturnStatus.DRAFT,
        db_index=True
    )

    # Supplier
    supplier = models.ForeignKey(
        'purchasing.Supplier',
        on_delete=models.PROTECT,
        related_name='purchase_returns'
    )

    # References
    purchase_order = models.ForeignKey(
        'purchasing.PurchaseOrder',
        on_delete=models.PROTECT,
        related_name='returns',
        null=True,
        blank=True
    )
    grn = models.ForeignKey(
        'purchasing.GoodsReceiptNote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns'
    )

    # Return Details
    return_date = models.DateField(default=timezone.now)
    reason = models.CharField(
        max_length=20,
        choices=ReturnReason.CHOICES,
        db_index=True
    )
    reason_detail = models.TextField(
        blank=True,
        help_text="Detailed description of the issue"
    )
    requested_action = models.CharField(
        max_length=10,
        choices=ReturnAction.CHOICES,
        default=ReturnAction.CREDIT
    )

    # Requestor
    requester_id = models.BigIntegerField(
        db_index=True,
        help_text="Employee ID of requester"
    )

    # RMA (Return Merchandise Authorization)
    rma_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Supplier's RMA/Return Authorization number"
    )
    rma_requested_at = models.DateTimeField(null=True, blank=True)
    rma_approved_at = models.DateTimeField(null=True, blank=True)
    rma_instructions = models.TextField(
        blank=True,
        help_text="Supplier's return instructions"
    )

    # Shipping
    shipping_date = models.DateField(null=True, blank=True)
    shipping_method = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier_name = models.CharField(max_length=200, blank=True)
    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Who bears the shipping cost"
    )
    shipping_paid_by = models.CharField(
        max_length=10,
        default='SUPPLIER',
        choices=[
            ('BUYER', 'Buyer'),
            ('SUPPLIER', 'Supplier'),
            ('SHARED', 'Shared'),
        ]
    )

    # Financials
    total_return_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    restocking_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    credit_note_number = models.CharField(max_length=100, blank=True)
    credit_note_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    credit_note_date = models.DateField(null=True, blank=True)

    # Approval
    approver_id = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    # Inventory Impact
    deduct_from_inventory = models.BooleanField(
        default=True,
        help_text="Deduct returned quantity from inventory"
    )
    inventory_transaction_id = models.BigIntegerField(
        null=True,
        blank=True
    )

    # Attachments
    attachment_photos = models.JSONField(default=list, blank=True)
    attachment_documents = models.JSONField(default=list, blank=True)

    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_return'
        verbose_name = 'Purchase Return'
        verbose_name_plural = 'Purchase Returns'
        ordering = ['-return_date', '-return_number']
        indexes = [
            models.Index(fields=['return_number'], name='ix_return_number'),
            models.Index(fields=['status'], name='ix_return_status'),
            models.Index(fields=['supplier'], name='ix_return_supplier'),
        ]

    def __str__(self):
        return f"{self.return_number} - {self.supplier.code}"

    def request_rma(self):
        """Request RMA from supplier"""
        if self.status == ReturnStatus.APPROVED:
            self.status = ReturnStatus.RMA_REQUESTED
            self.rma_requested_at = timezone.now()
            self.save(update_fields=['status', 'rma_requested_at'])
            return True
        return False

    def approve_rma(self, rma_number, instructions=''):
        """Record RMA approval from supplier"""
        if self.status == ReturnStatus.RMA_REQUESTED:
            self.status = ReturnStatus.RMA_APPROVED
            self.rma_number = rma_number
            self.rma_approved_at = timezone.now()
            self.rma_instructions = instructions
            self.save(update_fields=[
                'status', 'rma_number', 'rma_approved_at', 'rma_instructions'
            ])
            return True
        return False

    def mark_shipped(self, tracking_number='', carrier=''):
        """Mark return as shipped"""
        if self.status in [ReturnStatus.RMA_APPROVED, ReturnStatus.READY_TO_SHIP]:
            self.status = ReturnStatus.SHIPPED
            self.shipping_date = timezone.now().date()
            self.tracking_number = tracking_number
            self.carrier_name = carrier
            self.save(update_fields=[
                'status', 'shipping_date', 'tracking_number', 'carrier_name'
            ])
            return True
        return False

    def record_credit(self, credit_note_number, amount):
        """Record credit note received from supplier"""
        if self.status == ReturnStatus.RECEIVED_BY_SUPPLIER:
            self.status = ReturnStatus.CREDIT_RECEIVED
            self.credit_note_number = credit_note_number
            self.credit_note_amount = amount
            self.credit_note_date = timezone.now().date()
            self.save(update_fields=[
                'status', 'credit_note_number',
                'credit_note_amount', 'credit_note_date'
            ])
            return True
        return False

    def calculate_totals(self):
        """Calculate total return value from lines"""
        self.total_return_value = sum(
            line.total_value for line in self.lines.all()
        )
        self.save(update_fields=['total_return_value'])

    @classmethod
    def generate_return_number(cls):
        """Generate next return number"""
        year = timezone.now().year
        prefix = f'RET-{year}-'
        last_return = cls.all_objects.filter(
            return_number__startswith=prefix
        ).order_by('-return_number').first()

        if last_return:
            last_num = int(last_return.return_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class PurchaseReturnLine(AuditMixin):
    """
    Individual line item in a Purchase Return.
    """
    return_order = models.ForeignKey(
        PurchaseReturn,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()

    # Item Reference
    item_id = models.BigIntegerField(db_index=True)
    item_code = models.CharField(max_length=50)
    description = models.CharField(max_length=500)

    # Reference to original receipt
    grn_line = models.ForeignKey(
        'purchasing.GRNLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='return_lines'
    )
    po_line = models.ForeignKey(
        'purchasing.PurchaseOrderLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='return_lines'
    )

    # Quantities
    quantity_to_return = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    uom = models.CharField(max_length=20, default='EA')

    # Pricing
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Reason
    reason = models.CharField(
        max_length=20,
        choices=ReturnReason.CHOICES
    )
    defect_description = models.TextField(blank=True)

    # Serial/Batch
    serial_numbers = models.JSONField(
        default=list,
        blank=True,
        help_text="Serial numbers being returned"
    )
    batch_number = models.CharField(max_length=50, blank=True)

    # Storage
    current_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Current storage location of items"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_return_line'
        verbose_name = 'Return Line'
        verbose_name_plural = 'Return Lines'
        ordering = ['return_order', 'line_number']
        unique_together = [['return_order', 'line_number']]

    def __str__(self):
        return f"{self.return_order.return_number} Line {self.line_number}"

    def save(self, *args, **kwargs):
        # Calculate total value
        self.total_value = self.quantity_to_return * self.unit_price
        super().save(*args, **kwargs)
