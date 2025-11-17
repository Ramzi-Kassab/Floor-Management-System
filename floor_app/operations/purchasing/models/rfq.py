"""
Request for Quotation (RFQ) and Supplier Quotation Models

Manages the quotation process from suppliers for procurement.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .supplier import Currency, Incoterms, PaymentTerms


class RFQStatus:
    """RFQ status states"""
    DRAFT = 'DRAFT'
    SENT = 'SENT'
    PARTIALLY_QUOTED = 'PARTIALLY_QUOTED'
    FULLY_QUOTED = 'FULLY_QUOTED'
    CLOSED = 'CLOSED'
    CANCELLED = 'CANCELLED'

    CHOICES = [
        (DRAFT, 'Draft'),
        (SENT, 'Sent to Suppliers'),
        (PARTIALLY_QUOTED, 'Partially Quoted'),
        (FULLY_QUOTED, 'Fully Quoted'),
        (CLOSED, 'Closed'),
        (CANCELLED, 'Cancelled'),
    ]


class QuotationStatus:
    """Supplier Quotation status"""
    PENDING = 'PENDING'
    RECEIVED = 'RECEIVED'
    UNDER_EVALUATION = 'UNDER_EVALUATION'
    SELECTED = 'SELECTED'
    REJECTED = 'REJECTED'
    EXPIRED = 'EXPIRED'

    CHOICES = [
        (PENDING, 'Pending Response'),
        (RECEIVED, 'Received'),
        (UNDER_EVALUATION, 'Under Evaluation'),
        (SELECTED, 'Selected'),
        (REJECTED, 'Rejected'),
        (EXPIRED, 'Expired'),
    ]


class RequestForQuotation(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Request for Quotation (RFQ) sent to suppliers.
    Can be linked to PRs or created independently.
    """
    # Identification
    rfq_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Auto-generated RFQ number"
    )
    status = models.CharField(
        max_length=20,
        choices=RFQStatus.CHOICES,
        default=RFQStatus.DRAFT,
        db_index=True
    )
    title = models.CharField(max_length=200)

    # Dates
    issue_date = models.DateField(default=timezone.now)
    response_deadline = models.DateTimeField(
        help_text="Deadline for supplier responses"
    )
    validity_period_days = models.IntegerField(
        default=30,
        help_text="Required validity period for quotations"
    )

    # Buyer Information
    buyer_id = models.BigIntegerField(
        db_index=True,
        help_text="Employee ID of the buyer/procurement officer"
    )

    # Delivery Requirements
    required_delivery_date = models.DateField(
        null=True,
        blank=True
    )
    delivery_location_id = models.BigIntegerField(
        null=True,
        blank=True
    )
    delivery_address = models.TextField(blank=True)
    preferred_incoterm = models.CharField(
        max_length=3,
        choices=Incoterms.CHOICES,
        default=Incoterms.DAP,
        blank=True
    )

    # Terms
    preferred_payment_terms = models.CharField(
        max_length=20,
        choices=PaymentTerms.CHOICES,
        blank=True
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.CHOICES,
        default=Currency.SAR
    )

    # Instructions
    instructions = models.TextField(
        blank=True,
        help_text="Special instructions for suppliers"
    )
    technical_requirements = models.TextField(
        blank=True,
        help_text="Technical specifications and requirements"
    )
    commercial_terms = models.TextField(
        blank=True,
        help_text="Commercial terms and conditions"
    )

    # Statistics
    suppliers_invited = models.IntegerField(default=0)
    quotations_received = models.IntegerField(default=0)
    best_quote_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Reference to PR
    purchase_requisition = models.ForeignKey(
        'purchasing.PurchaseRequisition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rfqs'
    )

    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_rfq'
        verbose_name = 'Request for Quotation'
        verbose_name_plural = 'Requests for Quotation'
        ordering = ['-issue_date', '-rfq_number']
        indexes = [
            models.Index(fields=['rfq_number'], name='ix_rfq_number'),
            models.Index(fields=['status'], name='ix_rfq_status'),
            models.Index(fields=['buyer_id'], name='ix_rfq_buyer'),
        ]

    def __str__(self):
        return f"{self.rfq_number} - {self.title}"

    def is_deadline_passed(self):
        """Check if response deadline has passed"""
        return timezone.now() > self.response_deadline

    @classmethod
    def generate_rfq_number(cls):
        """Generate next RFQ number"""
        year = timezone.now().year
        prefix = f'RFQ-{year}-'
        last_rfq = cls.all_objects.filter(
            rfq_number__startswith=prefix
        ).order_by('-rfq_number').first()

        if last_rfq:
            last_num = int(last_rfq.rfq_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class RFQLine(AuditMixin):
    """
    Individual line item in an RFQ.
    """
    rfq = models.ForeignKey(
        RequestForQuotation,
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
    item_code = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=500)

    # Quantity
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    uom = models.CharField(max_length=20, default='EA')

    # Specifications
    specifications = models.TextField(
        blank=True,
        help_text="Technical specifications for this item"
    )

    # Reference to PR Line
    pr_line_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="PR Line that originated this RFQ line"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_rfq_line'
        verbose_name = 'RFQ Line'
        verbose_name_plural = 'RFQ Lines'
        ordering = ['rfq', 'line_number']
        unique_together = [['rfq', 'line_number']]

    def __str__(self):
        return f"{self.rfq.rfq_number} Line {self.line_number}"


class RFQSupplier(AuditMixin):
    """
    Suppliers invited to respond to an RFQ.
    """
    rfq = models.ForeignKey(
        RequestForQuotation,
        on_delete=models.CASCADE,
        related_name='invited_suppliers'
    )
    supplier = models.ForeignKey(
        'purchasing.Supplier',
        on_delete=models.CASCADE,
        related_name='rfq_invitations'
    )
    invited_at = models.DateTimeField(default=timezone.now)
    sent_via = models.CharField(
        max_length=20,
        default='EMAIL',
        choices=[
            ('EMAIL', 'Email'),
            ('FAX', 'Fax'),
            ('PORTAL', 'Supplier Portal'),
            ('MANUAL', 'Manual/Phone'),
        ]
    )
    response_received = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)
    decline_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_rfq_supplier'
        verbose_name = 'RFQ Supplier'
        verbose_name_plural = 'RFQ Suppliers'
        unique_together = [['rfq', 'supplier']]

    def __str__(self):
        return f"{self.rfq.rfq_number} - {self.supplier.code}"


class SupplierQuotation(PublicIdMixin, AuditMixin):
    """
    Quotation received from a supplier in response to an RFQ.
    """
    rfq = models.ForeignKey(
        RequestForQuotation,
        on_delete=models.CASCADE,
        related_name='quotations'
    )
    supplier = models.ForeignKey(
        'purchasing.Supplier',
        on_delete=models.CASCADE,
        related_name='quotations'
    )

    # Quotation Details
    quotation_number = models.CharField(
        max_length=50,
        help_text="Supplier's quotation/reference number"
    )
    status = models.CharField(
        max_length=20,
        choices=QuotationStatus.CHOICES,
        default=QuotationStatus.PENDING,
        db_index=True
    )

    # Dates
    received_date = models.DateField(null=True, blank=True)
    valid_until = models.DateField(
        null=True,
        blank=True,
        help_text="Quotation validity expiry date"
    )

    # Terms Offered
    currency = models.CharField(
        max_length=3,
        choices=Currency.CHOICES,
        default=Currency.SAR
    )
    payment_terms = models.CharField(
        max_length=20,
        choices=PaymentTerms.CHOICES,
        blank=True
    )
    incoterm = models.CharField(
        max_length=3,
        choices=Incoterms.CHOICES,
        blank=True
    )
    delivery_lead_time_days = models.IntegerField(
        default=0,
        help_text="Promised delivery lead time"
    )

    # Totals
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
    shipping_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Evaluation
    technical_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Technical evaluation score (0-100)"
    )
    commercial_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Commercial evaluation score (0-100)"
    )
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    evaluation_notes = models.TextField(blank=True)
    evaluated_by_id = models.BigIntegerField(null=True, blank=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    # Selection
    is_selected = models.BooleanField(default=False, db_index=True)
    selection_reason = models.TextField(blank=True)
    selected_by_id = models.BigIntegerField(null=True, blank=True)
    selected_at = models.DateTimeField(null=True, blank=True)

    # Attachment reference
    attachment_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to uploaded quotation document"
    )

    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_supplier_quotation'
        verbose_name = 'Supplier Quotation'
        verbose_name_plural = 'Supplier Quotations'
        ordering = ['-received_date']
        unique_together = [['rfq', 'supplier']]
        indexes = [
            models.Index(fields=['status'], name='ix_squo_status'),
            models.Index(fields=['is_selected'], name='ix_squo_selected'),
        ]

    def __str__(self):
        return f"{self.supplier.code} - {self.quotation_number}"

    def calculate_totals(self):
        """Recalculate totals from lines"""
        lines = self.lines.all()
        self.subtotal = sum(line.total_price for line in lines)
        self.total_amount = (
            self.subtotal - self.discount_amount +
            self.tax_amount + self.shipping_cost
        )
        self.save(update_fields=['subtotal', 'total_amount'])

    def select(self, selected_by_id, reason=''):
        """Mark this quotation as selected"""
        self.is_selected = True
        self.status = QuotationStatus.SELECTED
        self.selected_by_id = selected_by_id
        self.selected_at = timezone.now()
        self.selection_reason = reason
        self.save(update_fields=[
            'is_selected', 'status', 'selected_by_id',
            'selected_at', 'selection_reason'
        ])

        # Mark other quotations for the same RFQ as rejected
        SupplierQuotation.objects.filter(
            rfq=self.rfq
        ).exclude(pk=self.pk).update(status=QuotationStatus.REJECTED)


class SupplierQuotationLine(AuditMixin):
    """
    Individual line item in a supplier quotation.
    """
    quotation = models.ForeignKey(
        SupplierQuotation,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    rfq_line = models.ForeignKey(
        RFQLine,
        on_delete=models.CASCADE,
        related_name='quotation_lines'
    )
    line_number = models.PositiveIntegerField()

    # Quoted Details
    quantity_quoted = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
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

    # Supplier's Details
    supplier_part_number = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    brand = models.CharField(max_length=100, blank=True)

    # Lead Time
    lead_time_days = models.IntegerField(default=0)

    # Compliance
    meets_specifications = models.BooleanField(default=True)
    deviation_notes = models.TextField(
        blank=True,
        help_text="Any deviations from specifications"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_quotation_line'
        verbose_name = 'Quotation Line'
        verbose_name_plural = 'Quotation Lines'
        ordering = ['quotation', 'line_number']

    def __str__(self):
        return f"{self.quotation} Line {self.line_number}"

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity_quoted * self.unit_price
        super().save(*args, **kwargs)
