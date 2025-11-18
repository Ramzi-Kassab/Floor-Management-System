"""
Quotation Models - Job Card Costing & Customer Quotations

Replaces Excel "Quotation" sheet logic:
- Auto-calculates costs from cutter quantities, labor rates, and materials
- Supports customer-specific pricing and margins
- Preserves historical prices (quotations don't change when prices update)
- Tracks approval workflow
"""

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class Quotation(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Quotation/cost estimate for a job card.

    Automatically generated from:
    - Cutter quantities (from JobCutterEvaluationOverride or JobCutterEvaluationDetail)
    - Labor operations (from JobRoute steps)
    - Material/consumable estimates
    - Overhead and margin rates

    Excel mapping:
    - Quotation sheet → This model + QuotationLine
    - Formula-driven cost calculation → Python methods
    """

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('SENT_TO_CUSTOMER', 'Sent to Customer'),
        ('APPROVED', 'Approved by Customer'),
        ('REJECTED', 'Rejected by Customer'),
        ('REVISED', 'Revised/Superseded'),
        ('CANCELLED', 'Cancelled'),
    )

    # Core identification
    quotation_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique quotation number (auto-generated)"
    )

    # Link to job card
    job_card = models.ForeignKey(
        'JobCard',
        on_delete=models.PROTECT,
        related_name='quotations',
        help_text="Job card this quotation is for"
    )

    # Quotation metadata
    quotation_date = models.DateField(
        default=timezone.now,
        db_index=True,
        help_text="Date quotation was created"
    )
    valid_until_date = models.DateField(
        null=True,
        blank=True,
        help_text="Quotation validity expiration date"
    )

    # Customer information (denormalized for easy access)
    customer_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Customer name (from job card)"
    )
    customer_order_ref = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Customer's order reference"
    )

    # Cost breakdown (auto-calculated from QuotationLine)
    total_cutter_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Total cost of cutters"
    )
    total_labor_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Total labor cost"
    )
    total_material_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Total material/consumable cost"
    )

    # Subtotal before overhead and margin
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Cutters + Labor + Materials"
    )

    # Overhead and margin
    overhead_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        help_text="Overhead percentage (e.g., 15.00 for 15%)"
    )
    overhead_amount = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Calculated overhead amount"
    )

    margin_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00'),
        help_text="Profit margin percentage (e.g., 20.00 for 20%)"
    )
    margin_amount = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Calculated margin amount"
    )

    # Total
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Final total (subtotal + overhead + margin)"
    )

    currency = models.CharField(
        max_length=3,
        default='SAR',
        help_text="Currency code (ISO 4217)"
    )

    # Status and approval
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )

    sent_to_customer_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quotation was sent to customer"
    )
    sent_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations_sent',
        help_text="User who sent quotation to customer"
    )

    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When customer approved quotation"
    )
    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations_approved',
        help_text="User who recorded customer approval"
    )

    # Rejection tracking
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for customer rejection"
    )
    rejected_date = models.DateTimeField(
        null=True,
        blank=True
    )

    # Revision tracking
    revision_number = models.IntegerField(
        default=1,
        help_text="Revision number (1, 2, 3...)"
    )
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes',
        help_text="Newer quotation that replaces this one"
    )

    # Additional notes
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes about this quotation"
    )
    customer_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes to include in customer-facing quotation"
    )

    # Terms and conditions
    payment_terms = models.TextField(
        blank=True,
        default="",
        help_text="Payment terms (e.g., '30 days net')"
    )
    delivery_terms = models.TextField(
        blank=True,
        default="",
        help_text="Delivery terms and timeline"
    )

    class Meta:
        db_table = "production_quotation"
        verbose_name = "Quotation"
        verbose_name_plural = "Quotations"
        ordering = ['-quotation_date', '-created_at']
        unique_together = ['job_card', 'revision_number']
        indexes = [
            models.Index(fields=['quotation_number'], name='ix_quot_number'),
            models.Index(fields=['job_card'], name='ix_quot_job_card'),
            models.Index(fields=['status'], name='ix_quot_status'),
            models.Index(fields=['quotation_date'], name='ix_quot_date'),
        ]

    def __str__(self):
        return f"{self.quotation_number} - {self.job_card.job_card_number} Rev{self.revision_number}"

    @classmethod
    def generate_quotation_number(cls, job_card):
        """
        Generate a unique quotation number.

        Format: Q-{year}{month}-{job_card_number}-R{revision}
        Example: Q-202501-2025-ARDT-LV4-015-R1
        """
        from datetime import datetime
        prefix = datetime.now().strftime("Q-%Y%m")

        # Get current revision number for this job card
        last_quot = cls.objects.filter(job_card=job_card).order_by('-revision_number').first()
        revision = (last_quot.revision_number + 1) if last_quot else 1

        return f"{prefix}-{job_card.job_card_number}-R{revision}"

    def save(self, *args, **kwargs):
        """Auto-generate quotation number and set denormalized fields."""
        if not self.quotation_number:
            self.quotation_number = self.generate_quotation_number(self.job_card)

        # Denormalize customer info
        if self.job_card:
            self.customer_name = self.job_card.customer_name
            self.customer_order_ref = self.job_card.customer_order_ref

        super().save(*args, **kwargs)

    def recalculate_totals(self):
        """
        Recalculate all cost totals from quotation lines.

        Call this after adding/updating quotation lines.
        """
        lines = self.lines.all()

        # Sum by line type
        self.total_cutter_cost = lines.filter(
            line_type='CUTTER'
        ).aggregate(total=Sum('line_amount'))['total'] or Decimal('0.0000')

        self.total_labor_cost = lines.filter(
            line_type='LABOR'
        ).aggregate(total=Sum('line_amount'))['total'] or Decimal('0.0000')

        self.total_material_cost = lines.filter(
            line_type='MATERIAL'
        ).aggregate(total=Sum('line_amount'))['total'] or Decimal('0.0000')

        # Calculate subtotal
        self.subtotal = self.total_cutter_cost + self.total_labor_cost + self.total_material_cost

        # Calculate overhead
        self.overhead_amount = (self.subtotal * self.overhead_rate / Decimal('100.0')).quantize(Decimal('0.0001'))

        # Calculate margin
        self.margin_amount = (self.subtotal * self.margin_rate / Decimal('100.0')).quantize(Decimal('0.0001'))

        # Calculate total
        self.total_amount = self.subtotal + self.overhead_amount + self.margin_amount

        self.save(update_fields=[
            'total_cutter_cost', 'total_labor_cost', 'total_material_cost',
            'subtotal', 'overhead_amount', 'margin_amount', 'total_amount',
            'updated_at'
        ])

    def approve(self, user=None):
        """Mark quotation as approved by customer."""
        self.status = 'APPROVED'
        self.approved_date = timezone.now()
        self.approved_by = user
        self.save(update_fields=['status', 'approved_date', 'approved_by', 'updated_at'])

    def reject(self, reason='', user=None):
        """Mark quotation as rejected by customer."""
        self.status = 'REJECTED'
        self.rejection_reason = reason
        self.rejected_date = timezone.now()
        self.save(update_fields=['status', 'rejection_reason', 'rejected_date', 'updated_at'])

    def send_to_customer(self, user=None):
        """Mark quotation as sent to customer."""
        self.status = 'SENT_TO_CUSTOMER'
        self.sent_to_customer_date = timezone.now()
        self.sent_by = user
        self.save(update_fields=['status', 'sent_to_customer_date', 'sent_by', 'updated_at'])

    def create_revision(self):
        """
        Create a new revision of this quotation.

        Returns the new Quotation instance.
        """
        new_quot = Quotation.objects.create(
            job_card=self.job_card,
            quotation_date=timezone.now().date(),
            revision_number=self.revision_number + 1,
            overhead_rate=self.overhead_rate,
            margin_rate=self.margin_rate,
            customer_notes=self.customer_notes,
            payment_terms=self.payment_terms,
            delivery_terms=self.delivery_terms,
        )

        # Copy all lines from current quotation
        for line in self.lines.all():
            QuotationLine.objects.create(
                quotation=new_quot,
                line_number=line.line_number,
                line_type=line.line_type,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_amount=line.line_amount,
                item=line.item,
                operation=line.operation,
                notes=line.notes,
            )

        # Recalculate totals
        new_quot.recalculate_totals()

        # Mark current as superseded
        self.status = 'REVISED'
        self.superseded_by = new_quot
        self.save(update_fields=['status', 'superseded_by', 'updated_at'])

        return new_quot


class QuotationLine(AuditMixin):
    """
    Individual line item in a quotation.

    Line types:
    - CUTTER: Cutter replacement cost (quantity × unit price from CutterPriceHistory)
    - LABOR: Labor cost (hours × hourly rate for specific operation)
    - MATERIAL: Consumable material cost (brazing alloy, flux, etc.)
    - OVERHEAD: Overhead line (calculated, usually not stored as line)
    - MARGIN: Margin line (calculated, usually not stored as line)
    - OTHER: Other miscellaneous charges
    """

    LINE_TYPE_CHOICES = (
        ('CUTTER', 'Cutter'),
        ('LABOR', 'Labor'),
        ('MATERIAL', 'Material/Consumable'),
        ('OVERHEAD', 'Overhead'),
        ('MARGIN', 'Margin'),
        ('OTHER', 'Other'),
    )

    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent quotation"
    )

    line_number = models.IntegerField(
        help_text="Line sequence number (1, 2, 3...)"
    )

    line_type = models.CharField(
        max_length=10,
        choices=LINE_TYPE_CHOICES,
        db_index=True,
        help_text="Type of line item"
    )

    description = models.CharField(
        max_length=500,
        help_text="Line item description"
    )

    # Quantity and pricing
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=Decimal('1.0000'),
        help_text="Quantity (hours for labor, pieces for cutters)"
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Price per unit"
    )

    line_amount = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        help_text="Total line amount (quantity × unit_price)"
    )

    # Optional references
    item = models.ForeignKey(
        'inventory.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotation_lines',
        help_text="Item (for cutters and materials)"
    )

    operation = models.ForeignKey(
        'OperationDefinition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotation_lines',
        help_text="Operation (for labor lines)"
    )

    # Additional notes
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Line-specific notes"
    )

    class Meta:
        db_table = "production_quotation_line"
        verbose_name = "Quotation Line"
        verbose_name_plural = "Quotation Lines"
        ordering = ['quotation', 'line_number']
        unique_together = ['quotation', 'line_number']
        indexes = [
            models.Index(fields=['quotation', 'line_number'], name='ix_ql_quot_line'),
            models.Index(fields=['line_type'], name='ix_ql_type'),
        ]

    def __str__(self):
        return f"{self.quotation.quotation_number} Line {self.line_number}: {self.description}"

    def save(self, *args, **kwargs):
        """Auto-calculate line_amount."""
        self.line_amount = (self.quantity * self.unit_price).quantize(Decimal('0.0001'))
        super().save(*args, **kwargs)
