"""
Vendor Portal Models

Models for vendor management, RFQ, quotations, and procurement.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from floor_app.mixins import AuditMixin


class Vendor(AuditMixin):
    """Registered vendors/suppliers."""

    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('BLACKLISTED', 'Blacklisted'),
    )

    vendor_code = models.CharField(max_length=50, unique=True)
    company_name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    # Contact Information
    contact_person = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)

    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)

    # Categories
    categories = models.JSONField(default=list, help_text="Product/service categories")
    specializations = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_vendors')
    approval_date = models.DateField(null=True, blank=True)

    # Performance
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    total_rfqs_received = models.IntegerField(default=0)
    total_rfqs_responded = models.IntegerField(default=0)
    total_orders = models.IntegerField(default=0)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Banking
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    bank_details = models.JSONField(default=dict, blank=True)

    # Documents
    documents = models.JSONField(default=dict, blank=True)

    # Portal Access
    portal_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendor_profile')

    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'vendors'
        ordering = ['company_name']

    def __str__(self):
        return f"{self.vendor_code} - {self.company_name}"


class RFQ(AuditMixin):
    """Request for Quotation."""

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CLOSED', 'Closed'),
        ('AWARDED', 'Awarded'),
        ('CANCELLED', 'Cancelled'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    )

    rfq_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Requester
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='rfqs_requested')
    department = models.CharField(max_length=100, blank=True)
    project = models.CharField(max_length=100, blank=True)

    # Dates
    issue_date = models.DateField()
    submission_deadline = models.DateTimeField()
    required_delivery_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')

    # Invited Vendors
    invited_vendors = models.ManyToManyField(Vendor, related_name='rfqs_invited')
    published_publicly = models.BooleanField(default=False, help_text="Allow all vendors to submit")

    # Line Items
    line_items = models.JSONField(default=list, help_text="RFQ line items with specs")

    # Terms & Conditions
    payment_terms = models.TextField(blank=True)
    delivery_terms = models.TextField(blank=True)
    warranty_requirements = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)

    # Attachments
    attachments = models.JSONField(default=list, blank=True)

    # Evaluation Criteria
    evaluation_criteria = models.JSONField(default=dict, help_text="Criteria weights for evaluation")

    # Award
    awarded_vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='rfqs_won')
    awarded_quotation = models.ForeignKey('Quotation', on_delete=models.SET_NULL, null=True, blank=True, related_name='rfq_won')
    award_date = models.DateField(null=True, blank=True)
    award_notes = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'rfqs'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.rfq_number} - {self.title}"


class Quotation(AuditMixin):
    """Vendor quotation submission."""

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('SHORTLISTED', 'Shortlisted'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )

    quotation_number = models.CharField(max_length=50, unique=True)
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name='quotations')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='quotations')

    # Submission
    submitted_date = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='submitted_quotations')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    # Line Items (matching RFQ line items)
    line_items = models.JSONField(default=list, help_text="Quoted prices for RFQ items")

    # Pricing
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')

    # Terms
    payment_terms = models.TextField(blank=True)
    delivery_timeframe = models.CharField(max_length=200, blank=True)
    warranty = models.TextField(blank=True)
    validity_days = models.IntegerField(default=30, help_text="Quote valid for X days")

    # Documents
    documents = models.JSONField(default=list, blank=True)

    # Evaluation
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commercial_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    evaluation_notes = models.TextField(blank=True)
    evaluated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluated_quotations')
    evaluation_date = models.DateField(null=True, blank=True)

    # Rejection
    rejection_reason = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'quotations'
        unique_together = [['rfq', 'vendor']]
        ordering = ['-submitted_date']

    def __str__(self):
        return f"{self.quotation_number} - {self.vendor.company_name}"


class PurchaseOrder(AuditMixin):
    """Purchase Orders generated from accepted quotations."""

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Vendor'),
        ('ACKNOWLEDGED', 'Acknowledged by Vendor'),
        ('IN_PROGRESS', 'In Progress'),
        ('PARTIALLY_DELIVERED', 'Partially Delivered'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    po_number = models.CharField(max_length=50, unique=True)
    quotation = models.ForeignKey(Quotation, on_delete=models.PROTECT, related_name='purchase_orders')
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='purchase_orders')

    # Dates
    po_date = models.DateField()
    expected_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    # Line Items
    line_items = models.JSONField(default=list)

    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    # Terms
    payment_terms = models.TextField()
    delivery_terms = models.TextField()
    warranty_terms = models.TextField(blank=True)

    # Delivery
    shipping_address = models.TextField()
    billing_address = models.TextField()
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)

    # Approval
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_pos')
    approval_date = models.DateField(null=True, blank=True)

    # Vendor Acknowledgment
    acknowledged_date = models.DateField(null=True, blank=True)
    vendor_reference = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-po_date']

    def __str__(self):
        return f"{self.po_number} - {self.vendor.company_name}"


class VendorCommunication(AuditMixin):
    """Communication with vendors."""

    COMMUNICATION_TYPES = (
        ('EMAIL', 'Email'),
        ('PHONE', 'Phone Call'),
        ('MEETING', 'Meeting'),
        ('NOTE', 'Internal Note'),
        ('CLARIFICATION', 'Clarification Request'),
        ('UPDATE', 'Update'),
    )

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='communications')
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, null=True, blank=True, related_name='communications')
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, null=True, blank=True, related_name='communications')
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='communications')

    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPES)
    subject = models.CharField(max_length=200)
    message = models.TextField()

    # Sender
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='vendor_communications_sent')
    sent_date = models.DateTimeField(auto_now_add=True)

    # Response
    response = models.TextField(blank=True)
    responded_by = models.CharField(max_length=100, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)

    # Attachments
    attachments = models.JSONField(default=list, blank=True)

    is_internal = models.BooleanField(default=False, help_text="Internal note, not sent to vendor")

    class Meta:
        db_table = 'vendor_communications'
        ordering = ['-sent_date']

    def __str__(self):
        return f"{self.vendor.company_name} - {self.subject}"


class VendorPerformanceReview(AuditMixin):
    """Performance reviews for vendors."""

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='performance_reviews')
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='performance_reviews')

    review_date = models.DateField()
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    # Ratings (1-5)
    quality_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    delivery_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pricing_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2)

    # Comments
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    # Status
    would_recommend = models.BooleanField(default=True)

    class Meta:
        db_table = 'vendor_performance_reviews'
        ordering = ['-review_date']

    def __str__(self):
        return f"{self.vendor.company_name} - {self.review_date}"
