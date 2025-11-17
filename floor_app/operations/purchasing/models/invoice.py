"""
Supplier Invoice Models

Manages supplier invoices and three-way matching (PO ↔ GRN ↔ Invoice).
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .supplier import Currency, PaymentTerms


class InvoiceStatus:
    """Supplier Invoice status states"""
    DRAFT = 'DRAFT'
    RECEIVED = 'RECEIVED'
    UNDER_VERIFICATION = 'UNDER_VERIFICATION'
    VERIFIED = 'VERIFIED'
    DISPUTED = 'DISPUTED'
    APPROVED = 'APPROVED'
    PENDING_PAYMENT = 'PENDING_PAYMENT'
    PARTIALLY_PAID = 'PARTIALLY_PAID'
    PAID = 'PAID'
    CANCELLED = 'CANCELLED'

    CHOICES = [
        (DRAFT, 'Draft'),
        (RECEIVED, 'Received'),
        (UNDER_VERIFICATION, 'Under Verification'),
        (VERIFIED, 'Verified'),
        (DISPUTED, 'Disputed'),
        (APPROVED, 'Approved for Payment'),
        (PENDING_PAYMENT, 'Pending Payment'),
        (PARTIALLY_PAID, 'Partially Paid'),
        (PAID, 'Paid'),
        (CANCELLED, 'Cancelled'),
    ]


class PaymentStatus:
    """Payment status for invoice"""
    NOT_PAID = 'NOT_PAID'
    PARTIAL = 'PARTIAL'
    PAID = 'PAID'
    OVERDUE = 'OVERDUE'

    CHOICES = [
        (NOT_PAID, 'Not Paid'),
        (PARTIAL, 'Partially Paid'),
        (PAID, 'Paid in Full'),
        (OVERDUE, 'Overdue'),
    ]


class InvoiceType:
    """Types of supplier invoices"""
    STANDARD = 'STANDARD'
    PROFORMA = 'PROFORMA'
    CREDIT_NOTE = 'CREDIT_NOTE'
    DEBIT_NOTE = 'DEBIT_NOTE'

    CHOICES = [
        (STANDARD, 'Standard Invoice'),
        (PROFORMA, 'Proforma Invoice'),
        (CREDIT_NOTE, 'Credit Note'),
        (DEBIT_NOTE, 'Debit Note'),
    ]


class SupplierInvoice(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Supplier Invoice for three-way matching and payment processing.

    Three-way matching: PO ↔ GRN ↔ Invoice
    """
    # Identification
    invoice_number = models.CharField(
        max_length=100,
        help_text="Supplier's invoice number"
    )
    internal_reference = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Internal reference number"
    )
    invoice_type = models.CharField(
        max_length=15,
        choices=InvoiceType.CHOICES,
        default=InvoiceType.STANDARD
    )
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.CHOICES,
        default=InvoiceStatus.DRAFT,
        db_index=True
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.CHOICES,
        default=PaymentStatus.NOT_PAID,
        db_index=True
    )

    # Supplier
    supplier = models.ForeignKey(
        'purchasing.Supplier',
        on_delete=models.PROTECT,
        related_name='invoices'
    )

    # Dates
    invoice_date = models.DateField()
    received_date = models.DateField(default=timezone.now)
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Payment due date"
    )
    posting_date = models.DateField(
        default=timezone.now,
        help_text="Accounting posting date"
    )

    # References
    purchase_order = models.ForeignKey(
        'purchasing.PurchaseOrder',
        on_delete=models.PROTECT,
        related_name='invoices',
        null=True,
        blank=True
    )
    grn = models.ForeignKey(
        'purchasing.GoodsReceiptNote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )

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
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=1,
        help_text="Exchange rate to base currency (SAR)"
    )

    # Amounts
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    withholding_tax = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Withholding tax amount (if applicable)"
    )
    shipping_charges = models.DecimalField(
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
    amount_in_base_currency = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Payment Tracking
    amount_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    amount_outstanding = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    last_payment_date = models.DateField(null=True, blank=True)

    # Three-Way Matching
    is_matched = models.BooleanField(
        default=False,
        help_text="Invoice matched with PO and GRN"
    )
    matching_status = models.CharField(
        max_length=20,
        default='NOT_MATCHED',
        choices=[
            ('NOT_MATCHED', 'Not Matched'),
            ('PARTIAL_MATCH', 'Partial Match'),
            ('FULL_MATCH', 'Full Match'),
            ('DISCREPANCY', 'Discrepancy Found'),
        ]
    )
    quantity_variance = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text="Difference between invoiced and received quantity"
    )
    price_variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Difference between invoiced and PO price"
    )
    variance_notes = models.TextField(blank=True)

    # Verification
    verified_by_id = models.BigIntegerField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)

    # Approval
    approver_id = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    # Dispute
    is_disputed = models.BooleanField(default=False)
    dispute_reason = models.TextField(blank=True)
    disputed_at = models.DateTimeField(null=True, blank=True)
    dispute_resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    # Attachments
    attachment_invoice = models.CharField(max_length=500, blank=True)
    attachment_supporting_docs = models.JSONField(default=list, blank=True)

    # Accounting
    gl_account = models.CharField(
        max_length=50,
        blank=True,
        help_text="General Ledger account"
    )
    cost_center = models.CharField(max_length=50, blank=True)
    journal_entry_reference = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_supplier_invoice'
        verbose_name = 'Supplier Invoice'
        verbose_name_plural = 'Supplier Invoices'
        ordering = ['-invoice_date', '-internal_reference']
        unique_together = [['supplier', 'invoice_number']]
        indexes = [
            models.Index(fields=['internal_reference'], name='ix_sinv_ref'),
            models.Index(fields=['status'], name='ix_sinv_status'),
            models.Index(fields=['payment_status'], name='ix_sinv_payment'),
            models.Index(fields=['supplier'], name='ix_sinv_supplier'),
            models.Index(fields=['due_date'], name='ix_sinv_due_date'),
        ]

    def __str__(self):
        return f"{self.supplier.code} - {self.invoice_number}"

    def calculate_totals(self):
        """Recalculate totals from lines"""
        lines = self.lines.all()
        self.subtotal = sum(line.total_amount for line in lines)
        taxable = self.subtotal - self.discount_amount
        self.total_amount = (
            taxable + self.tax_amount - self.withholding_tax +
            self.shipping_charges + self.other_charges
        )
        self.amount_in_base_currency = self.total_amount * self.exchange_rate
        self.amount_outstanding = self.total_amount - self.amount_paid
        self.save(update_fields=[
            'subtotal', 'total_amount', 'amount_in_base_currency',
            'amount_outstanding'
        ])

    def perform_three_way_match(self):
        """
        Perform three-way matching between PO, GRN, and Invoice.
        Returns tuple of (is_matched, variance_details)
        """
        if not self.purchase_order or not self.grn:
            self.matching_status = 'NOT_MATCHED'
            self.is_matched = False
            self.save(update_fields=['matching_status', 'is_matched'])
            return False, "Missing PO or GRN reference"

        total_qty_variance = 0
        total_price_variance = 0
        discrepancies = []

        for inv_line in self.lines.all():
            # Find matching PO and GRN lines
            if inv_line.po_line:
                po_qty = inv_line.po_line.quantity_ordered
                po_price = inv_line.po_line.unit_price
            else:
                discrepancies.append(f"Line {inv_line.line_number}: No PO line reference")
                continue

            if inv_line.grn_line:
                grn_qty = inv_line.grn_line.quantity_accepted
            else:
                grn_qty = 0

            # Calculate variances
            qty_variance = inv_line.quantity_invoiced - grn_qty
            price_variance = (inv_line.unit_price - po_price) * inv_line.quantity_invoiced

            total_qty_variance += qty_variance
            total_price_variance += price_variance

            if qty_variance != 0:
                discrepancies.append(
                    f"Line {inv_line.line_number}: Qty variance {qty_variance}"
                )
            if price_variance != 0:
                discrepancies.append(
                    f"Line {inv_line.line_number}: Price variance {price_variance}"
                )

        self.quantity_variance = total_qty_variance
        self.price_variance = total_price_variance

        if total_qty_variance == 0 and total_price_variance == 0:
            self.matching_status = 'FULL_MATCH'
            self.is_matched = True
        elif discrepancies:
            self.matching_status = 'DISCREPANCY'
            self.is_matched = False
            self.variance_notes = '\n'.join(discrepancies)
        else:
            self.matching_status = 'PARTIAL_MATCH'
            self.is_matched = False

        self.save(update_fields=[
            'quantity_variance', 'price_variance', 'matching_status',
            'is_matched', 'variance_notes'
        ])

        return self.is_matched, self.variance_notes

    def verify(self, verifier_id, notes=''):
        """Mark invoice as verified"""
        if self.status in [InvoiceStatus.RECEIVED, InvoiceStatus.UNDER_VERIFICATION]:
            self.status = InvoiceStatus.VERIFIED
            self.verified_by_id = verifier_id
            self.verified_at = timezone.now()
            self.verification_notes = notes
            self.save(update_fields=[
                'status', 'verified_by_id', 'verified_at', 'verification_notes'
            ])
            return True
        return False

    def approve(self, approver_id, notes=''):
        """Approve invoice for payment"""
        if self.status == InvoiceStatus.VERIFIED:
            self.status = InvoiceStatus.APPROVED
            self.approver_id = approver_id
            self.approved_at = timezone.now()
            self.approval_notes = notes
            self.save(update_fields=[
                'status', 'approver_id', 'approved_at', 'approval_notes'
            ])
            return True
        return False

    def record_payment(self, amount, payment_date=None):
        """Record payment against invoice"""
        if payment_date is None:
            payment_date = timezone.now().date()

        self.amount_paid += amount
        self.amount_outstanding = self.total_amount - self.amount_paid
        self.last_payment_date = payment_date

        if self.amount_outstanding <= 0:
            self.payment_status = PaymentStatus.PAID
            self.status = InvoiceStatus.PAID
            self.amount_outstanding = 0
        else:
            self.payment_status = PaymentStatus.PARTIAL
            self.status = InvoiceStatus.PARTIALLY_PAID

        self.save(update_fields=[
            'amount_paid', 'amount_outstanding', 'last_payment_date',
            'payment_status', 'status'
        ])

    def check_overdue(self):
        """Check if invoice is overdue"""
        if (self.payment_status != PaymentStatus.PAID and
            self.due_date and
            self.due_date < timezone.now().date()):
            self.payment_status = PaymentStatus.OVERDUE
            self.save(update_fields=['payment_status'])
            return True
        return False

    @classmethod
    def generate_internal_reference(cls):
        """Generate next internal reference number"""
        year = timezone.now().year
        prefix = f'INV-{year}-'
        last_inv = cls.all_objects.filter(
            internal_reference__startswith=prefix
        ).order_by('-internal_reference').first()

        if last_inv:
            last_num = int(last_inv.internal_reference.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class SupplierInvoiceLine(AuditMixin):
    """
    Individual line item in a Supplier Invoice.
    """
    invoice = models.ForeignKey(
        SupplierInvoice,
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

    # References for matching
    po_line = models.ForeignKey(
        'purchasing.PurchaseOrderLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_lines'
    )
    grn_line = models.ForeignKey(
        'purchasing.GRNLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_lines'
    )

    # Invoiced Details
    quantity_invoiced = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    uom = models.CharField(max_length=20, default='EA')
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Tax
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15  # Saudi VAT
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Accounting
    gl_account = models.CharField(max_length=50, blank=True)
    cost_center = models.CharField(max_length=50, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_invoice_line'
        verbose_name = 'Invoice Line'
        verbose_name_plural = 'Invoice Lines'
        ordering = ['invoice', 'line_number']
        unique_together = [['invoice', 'line_number']]

    def __str__(self):
        return f"{self.invoice.internal_reference} Line {self.line_number}"

    def save(self, *args, **kwargs):
        # Calculate totals
        self.total_amount = self.quantity_invoiced * self.unit_price
        self.tax_amount = self.total_amount * (self.tax_rate / 100)
        super().save(*args, **kwargs)
