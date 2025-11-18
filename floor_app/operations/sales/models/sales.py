"""
Sales & Lifecycle - Sales Opportunities and Orders
Forecasting and order management.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin
from .customer import Customer, Rig, Well


class SalesOpportunity(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Sales opportunity/forecast for bits.
    Tracks potential orders before commitment.
    """
    STATUS_CHOICES = [
        ('IDENTIFIED', 'Identified'),
        ('QUALIFIED', 'Qualified'),
        ('QUOTED', 'Quote Sent'),
        ('NEGOTIATING', 'Negotiating'),
        ('WON', 'Won'),
        ('LOST', 'Lost'),
        ('ON_HOLD', 'On Hold'),
        ('CANCELLED', 'Cancelled'),
    ]

    PROBABILITY_CHOICES = [
        (10, '10% - Early Stage'),
        (25, '25% - Engaged'),
        (50, '50% - Proposal Sent'),
        (75, '75% - Verbal Commitment'),
        (90, '90% - Contract Review'),
        (100, '100% - Won'),
    ]

    # Identification
    opportunity_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Auto-generated opportunity ID"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")

    # Customer Context
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='opportunities'
    )
    well = models.ForeignKey(
        Well,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='opportunities'
    )
    rig = models.ForeignKey(
        Rig,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='opportunities'
    )
    field_name = models.CharField(max_length=100, blank=True, default="")

    # Bit Requirements
    bit_size_inches = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    bit_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="PDC, Roller Cone, etc."
    )
    mat_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Specific MAT if known"
    )
    quantity = models.PositiveIntegerField(default=1)
    application = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Drilling application/section"
    )

    # Status & Probability
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IDENTIFIED',
        db_index=True
    )
    probability = models.PositiveIntegerField(
        choices=PROBABILITY_CHOICES,
        default=10
    )

    # Value
    estimated_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Expected revenue in SAR"
    )
    currency = models.CharField(max_length=3, default='SAR')

    # Timing
    expected_order_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected order placement date"
    )
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected delivery/use date"
    )

    # Sales Team
    sales_rep = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sales_opportunities'
    )

    # Lost/Won Details
    closed_date = models.DateField(null=True, blank=True)
    close_reason = models.TextField(blank=True, default="")
    competitor = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Competitor who won (if lost)"
    )

    # Converted to Order
    converted_to_order = models.ForeignKey(
        'SalesOrder',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='source_opportunities'
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_opportunity"
        verbose_name = "Sales Opportunity"
        verbose_name_plural = "Sales Opportunities"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['opportunity_number'], name='ix_sales_opp_number'),
            models.Index(fields=['status'], name='ix_sales_opp_status'),
            models.Index(fields=['customer'], name='ix_sales_opp_customer'),
            models.Index(fields=['expected_delivery_date'], name='ix_sales_opp_deldate'),
        ]

    def __str__(self):
        return f"{self.opportunity_number} - {self.name}"

    @classmethod
    def generate_opportunity_number(cls):
        """Generate next opportunity number."""
        year = timezone.now().year
        prefix = f"OPP-{year}-"
        last_opp = cls.all_objects.filter(
            opportunity_number__startswith=prefix
        ).order_by('-opportunity_number').first()
        if last_opp:
            try:
                last_num = int(last_opp.opportunity_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}{next_num:04d}"

    @property
    def is_open(self):
        return self.status in ['IDENTIFIED', 'QUALIFIED', 'QUOTED', 'NEGOTIATING']

    @property
    def weighted_value(self):
        """Expected value weighted by probability."""
        return float(self.estimated_value) * (self.probability / 100)


class SalesOrder(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Confirmed sales order/commitment.
    Links customer orders to production.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_PRODUCTION', 'In Production'),
        ('PARTIAL_SHIPPED', 'Partially Shipped'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('INVOICED', 'Invoiced'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('RUSH', 'Rush'),
        ('HIGH', 'High'),
        ('NORMAL', 'Normal'),
        ('LOW', 'Low'),
    ]

    # Identification
    order_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Internal order number"
    )
    customer_po_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Customer's PO number"
    )

    # Customer
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='sales_orders'
    )
    billing_customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='billed_orders',
        help_text="Bill-to customer if different"
    )

    # Destination
    well = models.ForeignKey(
        Well,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sales_orders'
    )
    rig = models.ForeignKey(
        Rig,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sales_orders'
    )
    delivery_location = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Delivery address/location"
    )

    # Status & Priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='NORMAL'
    )

    # Dates
    order_date = models.DateField(default=timezone.now)
    required_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Customer's required date"
    )
    promised_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Our promised delivery date"
    )
    actual_delivery_date = models.DateField(null=True, blank=True)

    # Financials
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    currency = models.CharField(max_length=3, default='SAR')
    payment_terms_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override customer default"
    )

    # Production Link (loose coupling)
    batch_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to production.BatchOrder"
    )

    # Sales Team
    sales_rep = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sales_orders'
    )

    # Special Instructions
    special_instructions = models.TextField(blank=True, default="")
    quality_requirements = models.TextField(
        blank=True,
        default="",
        help_text="Customer-specific quality requirements"
    )

    # Invoice
    invoice_number = models.CharField(max_length=100, blank=True, default="")
    invoice_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_order"
        verbose_name = "Sales Order"
        verbose_name_plural = "Sales Orders"
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['order_number'], name='ix_sales_ord_number'),
            models.Index(fields=['customer_po_number'], name='ix_sales_ord_custpo'),
            models.Index(fields=['status'], name='ix_sales_ord_status'),
            models.Index(fields=['customer'], name='ix_sales_ord_customer'),
            models.Index(fields=['required_delivery_date'], name='ix_sales_ord_reqdate'),
        ]

    def __str__(self):
        return f"{self.order_number} - {self.customer.customer_code}"

    @classmethod
    def generate_order_number(cls):
        """Generate next order number."""
        year = timezone.now().year
        prefix = f"SO-{year}-"
        last_order = cls.all_objects.filter(
            order_number__startswith=prefix
        ).order_by('-order_number').first()
        if last_order:
            try:
                last_num = int(last_order.order_number.split('-')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}{next_num:05d}"

    @property
    def is_on_time(self):
        """Check if order is on track for delivery."""
        if self.actual_delivery_date and self.required_delivery_date:
            return self.actual_delivery_date <= self.required_delivery_date
        return None


class SalesOrderLine(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Line item on a sales order.
    Specifies bits/products ordered.
    """
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()

    # Product (loose coupling to inventory.Item)
    item_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to inventory.Item"
    )
    mat_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="MAT number if bit"
    )
    description = models.CharField(max_length=300)

    # Quantity
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_shipped = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    quantity_delivered = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    uom = models.CharField(max_length=20, default='PC')

    # Pricing
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    line_total = models.DecimalField(max_digits=15, decimal_places=2)

    # Assigned Serial Units (loose coupling)
    assigned_serial_numbers = models.TextField(
        blank=True,
        default="",
        help_text="Comma-separated serial numbers"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "sales_order_line"
        verbose_name = "Sales Order Line"
        verbose_name_plural = "Sales Order Lines"
        ordering = ['sales_order', 'line_number']
        unique_together = ['sales_order', 'line_number']
        indexes = [
            models.Index(fields=['sales_order'], name='ix_sales_ordln_order'),
            models.Index(fields=['mat_number'], name='ix_sales_ordln_mat'),
        ]

    def __str__(self):
        return f"{self.sales_order.order_number} Line {self.line_number}"

    def save(self, *args, **kwargs):
        """Calculate line total before saving."""
        if not self.line_total:
            subtotal = float(self.quantity_ordered) * float(self.unit_price)
            discount = subtotal * (float(self.discount_percent) / 100)
            self.line_total = subtotal - discount
        super().save(*args, **kwargs)

    @property
    def quantity_remaining(self):
        return float(self.quantity_ordered) - float(self.quantity_delivered)
