"""
Purchase Order (PO) Models

Core purchasing documents for ordering from suppliers.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .supplier import Currency, Incoterms, PaymentTerms


class POStatus:
    """Purchase Order status states"""
    DRAFT = 'DRAFT'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    SENT = 'SENT'
    ACKNOWLEDGED = 'ACKNOWLEDGED'
    PARTIALLY_RECEIVED = 'PARTIALLY_RECEIVED'
    FULLY_RECEIVED = 'FULLY_RECEIVED'
    CLOSED = 'CLOSED'
    CANCELLED = 'CANCELLED'

    CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (SENT, 'Sent to Supplier'),
        (ACKNOWLEDGED, 'Acknowledged by Supplier'),
        (PARTIALLY_RECEIVED, 'Partially Received'),
        (FULLY_RECEIVED, 'Fully Received'),
        (CLOSED, 'Closed'),
        (CANCELLED, 'Cancelled'),
    ]


class POType:
    """Purchase Order types"""
    STANDARD = 'STANDARD'
    BLANKET = 'BLANKET'
    CONTRACT = 'CONTRACT'
    SCHEDULED = 'SCHEDULED'

    CHOICES = [
        (STANDARD, 'Standard PO'),
        (BLANKET, 'Blanket/Framework PO'),
        (CONTRACT, 'Contract PO'),
        (SCHEDULED, 'Scheduled Release'),
    ]


class PurchaseOrder(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Purchase Order (PO) - Official order to supplier.

    Workflow: DRAFT → PENDING_APPROVAL → APPROVED → SENT → RECEIVED → CLOSED
    """
    # Identification
    po_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Auto-generated PO number"
    )
    po_type = models.CharField(
        max_length=20,
        choices=POType.CHOICES,
        default=POType.STANDARD
    )
    status = models.CharField(
        max_length=20,
        choices=POStatus.CHOICES,
        default=POStatus.DRAFT,
        db_index=True
    )

    # Supplier
    supplier = models.ForeignKey(
        'purchasing.Supplier',
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    supplier_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Supplier's reference/acknowledgement number"
    )

    # Buyer Information
    buyer_id = models.BigIntegerField(
        db_index=True,
        help_text="Employee ID of the buyer"
    )
    department_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True
    )

    # Dates
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField(
        null=True,
        blank=True
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True
    )

    # Delivery
    delivery_location_id = models.BigIntegerField(
        null=True,
        blank=True
    )
    delivery_address = models.TextField(blank=True)
    shipping_method = models.CharField(max_length=100, blank=True)

    # Terms
    currency = models.CharField(
        max_length=3,
        choices=Currency.CHOICES,
        default=Currency.SAR
    )
    payment_terms = models.CharField(
        max_length=20,
        choices=PaymentTerms.CHOICES,
        default=PaymentTerms.NET_30
    )
    incoterm = models.CharField(
        max_length=3,
        choices=Incoterms.CHOICES,
        default=Incoterms.DAP
    )

    # Financials
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15,  # Saudi VAT
        validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    shipping_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    other_charges = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Approval Workflow
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_pos'
    )

    approver_id = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    # Sent to Supplier
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_pos'
    )
    sent_via = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('EMAIL', 'Email'),
            ('FAX', 'Fax'),
            ('EDI', 'Electronic Data Interchange'),
            ('PORTAL', 'Supplier Portal'),
            ('MANUAL', 'Manual'),
        ]
    )

    # Acknowledgement
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledgement_notes = models.TextField(blank=True)

    # Cancellation
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_pos'
    )
    cancellation_reason = models.TextField(blank=True)

    # Closure
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_pos'
    )
    closure_notes = models.TextField(blank=True)

    # References
    purchase_requisition = models.ForeignKey(
        'purchasing.PurchaseRequisition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders'
    )
    supplier_quotation = models.ForeignKey(
        'purchasing.SupplierQuotation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders'
    )

    # Print & Communication
    print_count = models.IntegerField(default=0)
    last_printed_at = models.DateTimeField(null=True, blank=True)

    # Notes
    special_instructions = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_purchase_order'
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering = ['-order_date', '-po_number']
        indexes = [
            models.Index(fields=['po_number'], name='ix_po_number'),
            models.Index(fields=['status'], name='ix_po_status'),
            models.Index(fields=['supplier'], name='ix_po_supplier'),
            models.Index(fields=['buyer_id'], name='ix_po_buyer'),
            models.Index(fields=['order_date'], name='ix_po_date'),
        ]

    def __str__(self):
        return f"{self.po_number} - {self.supplier.code}"

    def calculate_totals(self):
        """Recalculate all totals from lines"""
        lines = self.lines.all()
        self.subtotal = sum(line.total_price for line in lines)
        self.discount_amount = self.subtotal * (self.discount_percentage / 100)
        taxable_amount = self.subtotal - self.discount_amount
        self.tax_amount = taxable_amount * (self.tax_percentage / 100)
        self.total_amount = (
            taxable_amount + self.tax_amount +
            self.shipping_cost + self.other_charges
        )
        self.save(update_fields=[
            'subtotal', 'discount_amount', 'tax_amount', 'total_amount'
        ])

    def submit_for_approval(self, user):
        """Submit PO for approval"""
        if self.status == POStatus.DRAFT:
            self.status = POStatus.PENDING_APPROVAL
            self.submitted_at = timezone.now()
            self.submitted_by = user
            self.save(update_fields=['status', 'submitted_at', 'submitted_by'])
            return True
        return False

    def approve(self, approver_id, notes=''):
        """Approve the PO"""
        if self.status == POStatus.PENDING_APPROVAL:
            self.status = POStatus.APPROVED
            self.approver_id = approver_id
            self.approved_at = timezone.now()
            self.approval_notes = notes
            self.save(update_fields=[
                'status', 'approver_id', 'approved_at', 'approval_notes'
            ])
            return True
        return False

    def send_to_supplier(self, user, method='EMAIL'):
        """Mark PO as sent to supplier"""
        if self.status in [POStatus.APPROVED, POStatus.SENT]:
            self.status = POStatus.SENT
            self.sent_at = timezone.now()
            self.sent_by = user
            self.sent_via = method
            self.save(update_fields=['status', 'sent_at', 'sent_by', 'sent_via'])
            return True
        return False

    def acknowledge(self, notes=''):
        """Mark PO as acknowledged by supplier"""
        if self.status == POStatus.SENT:
            self.status = POStatus.ACKNOWLEDGED
            self.acknowledged_at = timezone.now()
            self.acknowledgement_notes = notes
            self.save(update_fields=[
                'status', 'acknowledged_at', 'acknowledgement_notes'
            ])
            return True
        return False

    def cancel(self, user, reason):
        """Cancel the PO"""
        if self.status not in [POStatus.CLOSED, POStatus.CANCELLED]:
            self.status = POStatus.CANCELLED
            self.cancelled_at = timezone.now()
            self.cancelled_by = user
            self.cancellation_reason = reason
            self.save(update_fields=[
                'status', 'cancelled_at', 'cancelled_by', 'cancellation_reason'
            ])
            return True
        return False

    def close(self, user, notes=''):
        """Close the PO"""
        if self.status in [POStatus.FULLY_RECEIVED, POStatus.PARTIALLY_RECEIVED]:
            self.status = POStatus.CLOSED
            self.closed_at = timezone.now()
            self.closed_by = user
            self.closure_notes = notes
            self.save(update_fields=[
                'status', 'closed_at', 'closed_by', 'closure_notes'
            ])
            return True
        return False

    def update_receipt_status(self):
        """Update PO status based on line receipts"""
        lines = self.lines.all()
        if all(line.is_fully_received for line in lines):
            self.status = POStatus.FULLY_RECEIVED
        elif any(line.quantity_received > 0 for line in lines):
            self.status = POStatus.PARTIALLY_RECEIVED
        self.save(update_fields=['status'])

    @property
    def total_value_received(self):
        """Calculate total value of received items"""
        return sum(
            line.unit_price * line.quantity_received
            for line in self.lines.all()
        )

    @property
    def receiving_percentage(self):
        """Percentage of order received"""
        if self.subtotal == 0:
            return 0
        return (self.total_value_received / self.subtotal) * 100

    @classmethod
    def generate_po_number(cls):
        """Generate next PO number"""
        year = timezone.now().year
        prefix = f'PO-{year}-'
        last_po = cls.all_objects.filter(
            po_number__startswith=prefix
        ).order_by('-po_number').first()

        if last_po:
            last_num = int(last_po.po_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class PurchaseOrderLine(AuditMixin):
    """
    Individual line item in a Purchase Order.
    """
    po = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()

    # Item Reference
    item_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True
    )
    item_code = models.CharField(max_length=50)
    description = models.CharField(max_length=500)

    # Quantity
    quantity_ordered = models.DecimalField(
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
    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Receipt Tracking
    quantity_received = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    quantity_accepted = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text="Quantity accepted after inspection"
    )
    quantity_rejected = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    quantity_returned = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    is_fully_received = models.BooleanField(default=False)

    # Invoice Tracking
    quantity_invoiced = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    is_fully_invoiced = models.BooleanField(default=False)

    # Expected Delivery
    promised_date = models.DateField(null=True, blank=True)
    actual_date = models.DateField(null=True, blank=True)

    # References
    pr_line_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="PR Line reference"
    )
    quotation_line = models.ForeignKey(
        'purchasing.SupplierQuotationLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='po_lines'
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_po_line'
        verbose_name = 'PO Line'
        verbose_name_plural = 'PO Lines'
        ordering = ['po', 'line_number']
        unique_together = [['po', 'line_number']]
        indexes = [
            models.Index(fields=['po', 'line_number'], name='ix_poline_po_line'),
            models.Index(fields=['item_id'], name='ix_poline_item'),
        ]

    def __str__(self):
        return f"{self.po.po_number} Line {self.line_number}"

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity_ordered * self.unit_price

        # Check if fully received
        if self.quantity_received >= self.quantity_ordered:
            self.is_fully_received = True

        # Check if fully invoiced
        if self.quantity_invoiced >= self.quantity_ordered:
            self.is_fully_invoiced = True

        super().save(*args, **kwargs)

    @property
    def quantity_outstanding(self):
        """Quantity yet to be received"""
        return max(0, self.quantity_ordered - self.quantity_received)

    @property
    def value_outstanding(self):
        """Value of outstanding quantity"""
        return self.quantity_outstanding * self.unit_price
