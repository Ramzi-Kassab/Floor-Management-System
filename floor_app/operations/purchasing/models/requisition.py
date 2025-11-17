"""
Purchase Requisition Models

Internal request workflow for procurement of materials and services.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class PRStatus:
    """Purchase Requisition status states"""
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    UNDER_REVIEW = 'UNDER_REVIEW'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    PARTIALLY_ORDERED = 'PARTIALLY_ORDERED'
    FULLY_ORDERED = 'FULLY_ORDERED'
    CANCELLED = 'CANCELLED'
    CLOSED = 'CLOSED'

    CHOICES = [
        (DRAFT, 'Draft'),
        (SUBMITTED, 'Submitted'),
        (UNDER_REVIEW, 'Under Review'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (PARTIALLY_ORDERED, 'Partially Ordered'),
        (FULLY_ORDERED, 'Fully Ordered'),
        (CANCELLED, 'Cancelled'),
        (CLOSED, 'Closed'),
    ]


class PRPriority:
    """Requisition priority levels"""
    LOW = 'LOW'
    NORMAL = 'NORMAL'
    HIGH = 'HIGH'
    URGENT = 'URGENT'
    CRITICAL = 'CRITICAL'

    CHOICES = [
        (LOW, 'Low'),
        (NORMAL, 'Normal'),
        (HIGH, 'High'),
        (URGENT, 'Urgent'),
        (CRITICAL, 'Critical'),
    ]


class PRType:
    """Purchase Requisition types"""
    STOCK = 'STOCK'
    NON_STOCK = 'NON_STOCK'
    SERVICE = 'SERVICE'
    CAPEX = 'CAPEX'
    PROJECT = 'PROJECT'
    MRO = 'MRO'

    CHOICES = [
        (STOCK, 'Stock Item'),
        (NON_STOCK, 'Non-Stock Item'),
        (SERVICE, 'Service'),
        (CAPEX, 'Capital Expenditure'),
        (PROJECT, 'Project Material'),
        (MRO, 'Maintenance, Repair & Operations'),
    ]


class PurchaseRequisition(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Purchase Requisition (PR) - Internal request for procurement.

    Workflow: DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED → ORDERED → CLOSED
    """
    # Identification
    pr_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Auto-generated PR number (e.g., PR-2024-00001)"
    )
    pr_type = models.CharField(
        max_length=20,
        choices=PRType.CHOICES,
        default=PRType.STOCK,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=PRStatus.CHOICES,
        default=PRStatus.DRAFT,
        db_index=True
    )
    priority = models.CharField(
        max_length=10,
        choices=PRPriority.CHOICES,
        default=PRPriority.NORMAL,
        db_index=True
    )

    # Requester Information
    requester_id = models.BigIntegerField(
        db_index=True,
        help_text="Employee ID of the requester"
    )
    department_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Department ID from HR module"
    )
    cost_center = models.CharField(max_length=50, blank=True)
    project_code = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="Project/Job code if applicable"
    )

    # Dates
    request_date = models.DateField(default=timezone.now)
    required_by_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date by which items are needed"
    )

    # Delivery Information
    delivery_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Warehouse/Location ID for delivery"
    )
    delivery_address = models.TextField(
        blank=True,
        help_text="Override delivery address if not standard location"
    )

    # Approval Workflow
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_prs'
    )

    first_approver_id = models.BigIntegerField(null=True, blank=True)
    first_approval_at = models.DateTimeField(null=True, blank=True)
    first_approval_notes = models.TextField(blank=True)

    second_approver_id = models.BigIntegerField(null=True, blank=True)
    second_approval_at = models.DateTimeField(null=True, blank=True)
    second_approval_notes = models.TextField(blank=True)

    final_approver_id = models.BigIntegerField(null=True, blank=True)
    final_approval_at = models.DateTimeField(null=True, blank=True)
    final_approval_notes = models.TextField(blank=True)

    rejected_by_id = models.BigIntegerField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Totals (calculated from lines)
    total_estimated_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    currency = models.CharField(max_length=3, default='SAR')

    # Reference to production/planning
    job_card_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Related Job Card if material is for production"
    )

    # Notes
    justification = models.TextField(
        blank=True,
        help_text="Business justification for the purchase"
    )
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_purchase_requisition'
        verbose_name = 'Purchase Requisition'
        verbose_name_plural = 'Purchase Requisitions'
        ordering = ['-request_date', '-pr_number']
        indexes = [
            models.Index(fields=['pr_number'], name='ix_pr_number'),
            models.Index(fields=['status'], name='ix_pr_status'),
            models.Index(fields=['requester_id'], name='ix_pr_requester'),
            models.Index(fields=['department_id'], name='ix_pr_department'),
            models.Index(fields=['request_date'], name='ix_pr_date'),
        ]

    def __str__(self):
        return f"{self.pr_number} - {self.get_status_display()}"

    def submit(self, user):
        """Submit PR for approval"""
        if self.status == PRStatus.DRAFT:
            self.status = PRStatus.SUBMITTED
            self.submitted_at = timezone.now()
            self.submitted_by = user
            self.save(update_fields=['status', 'submitted_at', 'submitted_by'])
            return True
        return False

    def approve_first_level(self, approver_id, notes=''):
        """First level approval"""
        if self.status == PRStatus.SUBMITTED:
            self.status = PRStatus.UNDER_REVIEW
            self.first_approver_id = approver_id
            self.first_approval_at = timezone.now()
            self.first_approval_notes = notes
            self.save(update_fields=[
                'status', 'first_approver_id',
                'first_approval_at', 'first_approval_notes'
            ])
            return True
        return False

    def approve_final(self, approver_id, notes=''):
        """Final approval"""
        if self.status in [PRStatus.SUBMITTED, PRStatus.UNDER_REVIEW]:
            self.status = PRStatus.APPROVED
            self.final_approver_id = approver_id
            self.final_approval_at = timezone.now()
            self.final_approval_notes = notes
            self.save(update_fields=[
                'status', 'final_approver_id',
                'final_approval_at', 'final_approval_notes'
            ])
            return True
        return False

    def reject(self, rejector_id, reason):
        """Reject PR"""
        if self.status in [PRStatus.SUBMITTED, PRStatus.UNDER_REVIEW]:
            self.status = PRStatus.REJECTED
            self.rejected_by_id = rejector_id
            self.rejected_at = timezone.now()
            self.rejection_reason = reason
            self.save(update_fields=[
                'status', 'rejected_by_id',
                'rejected_at', 'rejection_reason'
            ])
            return True
        return False

    def calculate_totals(self):
        """Recalculate total estimated value from lines"""
        total = sum(
            line.total_estimated_cost
            for line in self.lines.all()
        )
        self.total_estimated_value = total
        self.save(update_fields=['total_estimated_value'])

    @classmethod
    def generate_pr_number(cls):
        """Generate next PR number"""
        year = timezone.now().year
        prefix = f'PR-{year}-'
        last_pr = cls.all_objects.filter(
            pr_number__startswith=prefix
        ).order_by('-pr_number').first()

        if last_pr:
            last_num = int(last_pr.pr_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class PurchaseRequisitionLine(AuditMixin):
    """
    Individual line item in a Purchase Requisition.
    """
    pr = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()

    # Item Reference
    item_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Reference to Item in inventory"
    )
    item_code = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=500)

    # Quantity
    quantity_requested = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    uom = models.CharField(
        max_length=20,
        default='EA',
        help_text="Unit of Measure"
    )

    # Estimated Cost
    estimated_unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_estimated_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Preferred Supplier (suggestion)
    suggested_supplier_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True
    )

    # Ordering Status
    quantity_ordered = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text="Quantity already ordered via PO"
    )
    is_fully_ordered = models.BooleanField(default=False)

    # Reference
    bom_line_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="BOM Line reference if from production"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_pr_line'
        verbose_name = 'PR Line'
        verbose_name_plural = 'PR Lines'
        ordering = ['pr', 'line_number']
        unique_together = [['pr', 'line_number']]
        indexes = [
            models.Index(fields=['pr', 'line_number'], name='ix_prline_pr_line'),
            models.Index(fields=['item_id'], name='ix_prline_item'),
        ]

    def __str__(self):
        return f"{self.pr.pr_number} Line {self.line_number}"

    def save(self, *args, **kwargs):
        # Calculate total estimated cost
        self.total_estimated_cost = (
            self.quantity_requested * self.estimated_unit_price
        )
        # Check if fully ordered
        if self.quantity_ordered >= self.quantity_requested:
            self.is_fully_ordered = True
        super().save(*args, **kwargs)

    @property
    def quantity_remaining(self):
        """Quantity yet to be ordered"""
        return max(0, self.quantity_requested - self.quantity_ordered)
