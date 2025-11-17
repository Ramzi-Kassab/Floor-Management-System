"""
Supplier & Catalog Management Models

Manages suppliers, their products, and commercial terms for PDC bit manufacturing.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class SupplierClassification:
    """Supplier classification types"""
    LOCAL = 'LOCAL'
    INTERNATIONAL = 'INTERNATIONAL'
    OEM = 'OEM'
    JV_PARTNER = 'JV_PARTNER'
    SERVICE_PROVIDER = 'SERVICE_PROVIDER'

    CHOICES = [
        (LOCAL, 'Local Supplier'),
        (INTERNATIONAL, 'International Supplier'),
        (OEM, 'Original Equipment Manufacturer'),
        (JV_PARTNER, 'Joint Venture Partner'),
        (SERVICE_PROVIDER, 'Service Provider'),
    ]


class SupplierStatus:
    """Supplier status states"""
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    BLACKLISTED = 'BLACKLISTED'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    UNDER_EVALUATION = 'UNDER_EVALUATION'

    CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (BLACKLISTED, 'Blacklisted'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (UNDER_EVALUATION, 'Under Evaluation'),
    ]


class PaymentTerms:
    """Standard payment terms"""
    NET_30 = 'NET_30'
    NET_45 = 'NET_45'
    NET_60 = 'NET_60'
    NET_90 = 'NET_90'
    PREPAID = 'PREPAID'
    COD = 'COD'
    LC_AT_SIGHT = 'LC_AT_SIGHT'
    LC_30 = 'LC_30'
    LC_60 = 'LC_60'
    LC_90 = 'LC_90'

    CHOICES = [
        (NET_30, 'Net 30 Days'),
        (NET_45, 'Net 45 Days'),
        (NET_60, 'Net 60 Days'),
        (NET_90, 'Net 90 Days'),
        (PREPAID, 'Prepaid'),
        (COD, 'Cash on Delivery'),
        (LC_AT_SIGHT, 'Letter of Credit - At Sight'),
        (LC_30, 'Letter of Credit - 30 Days'),
        (LC_60, 'Letter of Credit - 60 Days'),
        (LC_90, 'Letter of Credit - 90 Days'),
    ]


class Incoterms:
    """International Commercial Terms"""
    EXW = 'EXW'
    FCA = 'FCA'
    CPT = 'CPT'
    CIP = 'CIP'
    DAP = 'DAP'
    DPU = 'DPU'
    DDP = 'DDP'
    FAS = 'FAS'
    FOB = 'FOB'
    CFR = 'CFR'
    CIF = 'CIF'

    CHOICES = [
        (EXW, 'EXW - Ex Works'),
        (FCA, 'FCA - Free Carrier'),
        (CPT, 'CPT - Carriage Paid To'),
        (CIP, 'CIP - Carriage and Insurance Paid To'),
        (DAP, 'DAP - Delivered at Place'),
        (DPU, 'DPU - Delivered at Place Unloaded'),
        (DDP, 'DDP - Delivered Duty Paid'),
        (FAS, 'FAS - Free Alongside Ship'),
        (FOB, 'FOB - Free on Board'),
        (CFR, 'CFR - Cost and Freight'),
        (CIF, 'CIF - Cost, Insurance and Freight'),
    ]


class Currency:
    """Common currencies for Saudi Arabia operations"""
    SAR = 'SAR'
    USD = 'USD'
    EUR = 'EUR'
    GBP = 'GBP'
    AED = 'AED'
    CNY = 'CNY'
    JPY = 'JPY'

    CHOICES = [
        (SAR, 'Saudi Riyal (SAR)'),
        (USD, 'US Dollar (USD)'),
        (EUR, 'Euro (EUR)'),
        (GBP, 'British Pound (GBP)'),
        (AED, 'UAE Dirham (AED)'),
        (CNY, 'Chinese Yuan (CNY)'),
        (JPY, 'Japanese Yen (JPY)'),
    ]


class Supplier(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Supplier master data for procurement.

    Tracks supplier information including contact details, commercial terms,
    certifications, and performance metrics.
    """
    # Basic Information
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique supplier code (e.g., SUP-001)"
    )
    name = models.CharField(max_length=200, db_index=True)
    legal_name = models.CharField(max_length=200, blank=True)
    classification = models.CharField(
        max_length=20,
        choices=SupplierClassification.CHOICES,
        default=SupplierClassification.LOCAL,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=SupplierStatus.CHOICES,
        default=SupplierStatus.PENDING_APPROVAL,
        db_index=True
    )

    # Contact Information
    primary_email = models.EmailField(blank=True)
    secondary_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)

    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Saudi Arabia')

    # Commercial Terms
    default_currency = models.CharField(
        max_length=3,
        choices=Currency.CHOICES,
        default=Currency.SAR
    )
    payment_terms = models.CharField(
        max_length=20,
        choices=PaymentTerms.CHOICES,
        default=PaymentTerms.NET_30
    )
    default_incoterm = models.CharField(
        max_length=3,
        choices=Incoterms.CHOICES,
        default=Incoterms.DAP,
        blank=True
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Credit limit in default currency"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Tax & Registration
    tax_id = models.CharField(max_length=50, blank=True, help_text="VAT/Tax Registration Number")
    cr_number = models.CharField(max_length=50, blank=True, help_text="Commercial Registration Number")
    gosi_number = models.CharField(max_length=50, blank=True, help_text="GOSI Registration (Saudi Arabia)")
    saudization_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Saudization percentage for local suppliers"
    )

    # Banking Information
    bank_name = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_iban = models.CharField(max_length=50, blank=True)
    bank_swift_code = models.CharField(max_length=20, blank=True)

    # Certifications & Qualifications
    iso_certified = models.BooleanField(default=False)
    iso_certificate_number = models.CharField(max_length=100, blank=True)
    iso_expiry_date = models.DateField(null=True, blank=True)
    api_certified = models.BooleanField(default=False, help_text="API certification for oil & gas")
    api_certificate_number = models.CharField(max_length=100, blank=True)
    api_expiry_date = models.DateField(null=True, blank=True)
    other_certifications = models.JSONField(default=dict, blank=True)

    # Performance Metrics
    average_lead_time_days = models.IntegerField(default=0)
    on_time_delivery_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    quality_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Rating out of 5"
    )
    total_orders = models.IntegerField(default=0)
    total_value_purchased = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    last_order_date = models.DateField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes not shared with supplier")

    class Meta:
        db_table = 'purchasing_supplier'
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code'], name='ix_supplier_code'),
            models.Index(fields=['name'], name='ix_supplier_name'),
            models.Index(fields=['status'], name='ix_supplier_status'),
            models.Index(fields=['classification'], name='ix_supplier_class'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_full_address(self):
        """Return formatted full address"""
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state_province} {self.postal_code}".strip(),
            self.country
        ]
        return '\n'.join(p for p in parts if p.strip())

    def update_performance_metrics(self, on_time=True, quality_score=None):
        """Update supplier performance metrics after an order"""
        self.total_orders += 1
        if on_time:
            # Recalculate on-time delivery percentage
            on_time_count = (self.on_time_delivery_percentage / 100) * (self.total_orders - 1)
            on_time_count += 1
            self.on_time_delivery_percentage = (on_time_count / self.total_orders) * 100
        else:
            on_time_count = (self.on_time_delivery_percentage / 100) * (self.total_orders - 1)
            self.on_time_delivery_percentage = (on_time_count / self.total_orders) * 100

        if quality_score is not None:
            # Running average for quality rating
            total_score = self.quality_rating * (self.total_orders - 1)
            total_score += quality_score
            self.quality_rating = total_score / self.total_orders

        self.save(update_fields=[
            'total_orders',
            'on_time_delivery_percentage',
            'quality_rating',
            'last_order_date'
        ])


class SupplierContact(AuditMixin):
    """
    Contact persons for a supplier.
    Multiple contacts can be assigned to different roles.
    """
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    is_primary = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_supplier_contact'
        verbose_name = 'Supplier Contact'
        verbose_name_plural = 'Supplier Contacts'
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.supplier.code})"

    def save(self, *args, **kwargs):
        # Ensure only one primary contact per supplier
        if self.is_primary:
            SupplierContact.objects.filter(
                supplier=self.supplier,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class SupplierItem(AuditMixin):
    """
    Supplier-Item catalog mapping.
    Links items from inventory to their suppliers with pricing and terms.
    """
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='supplier_items'
    )
    # Reference to Item in inventory module
    item_id = models.BigIntegerField(db_index=True)

    # Supplier's product details
    supplier_part_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Supplier's part/SKU number"
    )
    supplier_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Supplier's product description"
    )

    # Pricing
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.CHOICES,
        default=Currency.SAR
    )
    price_valid_from = models.DateField(null=True, blank=True)
    price_valid_until = models.DateField(null=True, blank=True)
    last_price_update = models.DateTimeField(null=True, blank=True)

    # Ordering constraints
    minimum_order_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Minimum order quantity (MOQ)"
    )
    order_multiple = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Order must be in multiples of this quantity"
    )
    pack_size = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Standard pack/box size"
    )

    # Lead times
    lead_time_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Standard lead time in days"
    )
    safety_lead_time_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Additional safety buffer days"
    )

    # Preferences
    is_preferred = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Preferred supplier for this item"
    )
    is_active = models.BooleanField(default=True, db_index=True)

    # Quality & Compliance
    quality_grade = models.CharField(max_length=20, blank=True)
    requires_inspection = models.BooleanField(
        default=False,
        help_text="Item requires quality inspection on receipt"
    )
    inspection_plan = models.TextField(
        blank=True,
        help_text="Inspection criteria and procedures"
    )

    # Performance
    average_actual_lead_time = models.IntegerField(default=0)
    defect_rate_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_supplier_item'
        verbose_name = 'Supplier Item'
        verbose_name_plural = 'Supplier Items'
        unique_together = [['supplier', 'item_id']]
        ordering = ['supplier', '-is_preferred']
        indexes = [
            models.Index(fields=['supplier', 'item_id'], name='ix_supitem_sup_item'),
            models.Index(fields=['item_id'], name='ix_supitem_item'),
            models.Index(fields=['is_preferred'], name='ix_supitem_preferred'),
        ]

    def __str__(self):
        return f"{self.supplier.code} - Item #{self.item_id}"

    @property
    def total_lead_time(self):
        """Total lead time including safety buffer"""
        return self.lead_time_days + self.safety_lead_time_days

    def get_price_for_quantity(self, quantity):
        """
        Calculate price for given quantity.
        Can be extended for quantity-based discounts.
        """
        return self.unit_price * quantity
