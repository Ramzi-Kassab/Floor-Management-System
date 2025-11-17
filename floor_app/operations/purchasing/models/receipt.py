"""
Goods Receipt Note (GRN) and Quality Inspection Models

Manages receipt of goods from suppliers and quality inspection workflow.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class GRNStatus:
    """GRN status states"""
    DRAFT = 'DRAFT'
    PENDING_INSPECTION = 'PENDING_INSPECTION'
    UNDER_INSPECTION = 'UNDER_INSPECTION'
    INSPECTION_COMPLETE = 'INSPECTION_COMPLETE'
    POSTED = 'POSTED'
    CANCELLED = 'CANCELLED'

    CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_INSPECTION, 'Pending Inspection'),
        (UNDER_INSPECTION, 'Under Inspection'),
        (INSPECTION_COMPLETE, 'Inspection Complete'),
        (POSTED, 'Posted to Inventory'),
        (CANCELLED, 'Cancelled'),
    ]


class InspectionStatus:
    """Quality Inspection status"""
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    PASSED = 'PASSED'
    FAILED = 'FAILED'
    CONDITIONAL = 'CONDITIONAL'

    CHOICES = [
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In Progress'),
        (PASSED, 'Passed'),
        (FAILED, 'Failed'),
        (CONDITIONAL, 'Conditional Accept'),
    ]


class InspectionResult:
    """Inspection result types"""
    ACCEPT = 'ACCEPT'
    REJECT = 'REJECT'
    ACCEPT_WITH_DEVIATION = 'ACCEPT_WITH_DEVIATION'
    REWORK = 'REWORK'
    USE_AS_IS = 'USE_AS_IS'

    CHOICES = [
        (ACCEPT, 'Accept'),
        (REJECT, 'Reject'),
        (ACCEPT_WITH_DEVIATION, 'Accept with Deviation'),
        (REWORK, 'Rework Required'),
        (USE_AS_IS, 'Use As-Is'),
    ]


class GoodsReceiptNote(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Goods Receipt Note (GRN) - Document for receiving goods from supplier.

    Workflow: DRAFT → PENDING_INSPECTION → INSPECTION_COMPLETE → POSTED
    """
    # Identification
    grn_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Auto-generated GRN number"
    )
    status = models.CharField(
        max_length=25,
        choices=GRNStatus.CHOICES,
        default=GRNStatus.DRAFT,
        db_index=True
    )

    # Reference to Purchase Order
    purchase_order = models.ForeignKey(
        'purchasing.PurchaseOrder',
        on_delete=models.PROTECT,
        related_name='grns'
    )

    # Receipt Details
    receipt_date = models.DateField(default=timezone.now)
    receipt_time = models.TimeField(default=timezone.now)
    received_by_id = models.BigIntegerField(
        db_index=True,
        help_text="Employee ID who received the goods"
    )

    # Shipping Information
    delivery_note_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Supplier's delivery note/packing slip number"
    )
    waybill_number = models.CharField(max_length=100, blank=True)
    carrier_name = models.CharField(max_length=200, blank=True)
    vehicle_number = models.CharField(max_length=50, blank=True)
    driver_name = models.CharField(max_length=200, blank=True)
    driver_id = models.CharField(max_length=50, blank=True)

    # Location
    receiving_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Warehouse/Location where goods received"
    )
    qa_hold_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="QA Hold location for inspection"
    )

    # Package Information
    total_packages = models.IntegerField(default=0)
    total_weight_kg = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0
    )
    package_condition = models.CharField(
        max_length=50,
        default='GOOD',
        choices=[
            ('EXCELLENT', 'Excellent'),
            ('GOOD', 'Good'),
            ('DAMAGED', 'Damaged'),
            ('SEVERELY_DAMAGED', 'Severely Damaged'),
        ]
    )
    damage_notes = models.TextField(blank=True)

    # Inspection
    requires_inspection = models.BooleanField(default=True)
    inspection_status = models.CharField(
        max_length=20,
        choices=InspectionStatus.CHOICES,
        default=InspectionStatus.PENDING
    )
    inspection_completed_at = models.DateTimeField(null=True, blank=True)
    inspected_by_id = models.BigIntegerField(null=True, blank=True)

    # Posting
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_grns'
    )
    inventory_transaction_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Reference to inventory transaction created"
    )

    # Customs & Compliance (Saudi Arabia)
    customs_declaration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Saudi Customs declaration number"
    )
    customs_clearance_date = models.DateField(null=True, blank=True)
    import_permit_number = models.CharField(max_length=100, blank=True)
    certificate_of_origin = models.CharField(max_length=100, blank=True)
    certificate_of_conformity = models.CharField(max_length=100, blank=True)

    # Attachments
    attachment_delivery_note = models.CharField(max_length=500, blank=True)
    attachment_customs_docs = models.CharField(max_length=500, blank=True)
    attachment_photos = models.JSONField(default=list, blank=True)

    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_grn'
        verbose_name = 'Goods Receipt Note'
        verbose_name_plural = 'Goods Receipt Notes'
        ordering = ['-receipt_date', '-grn_number']
        indexes = [
            models.Index(fields=['grn_number'], name='ix_grn_number'),
            models.Index(fields=['status'], name='ix_grn_status'),
            models.Index(fields=['receipt_date'], name='ix_grn_date'),
        ]

    def __str__(self):
        return f"{self.grn_number} - PO: {self.purchase_order.po_number}"

    def start_inspection(self):
        """Start inspection process"""
        if self.status == GRNStatus.PENDING_INSPECTION:
            self.status = GRNStatus.UNDER_INSPECTION
            self.inspection_status = InspectionStatus.IN_PROGRESS
            self.save(update_fields=['status', 'inspection_status'])
            return True
        return False

    def complete_inspection(self, inspector_id):
        """Mark inspection as complete"""
        if self.status == GRNStatus.UNDER_INSPECTION:
            self.status = GRNStatus.INSPECTION_COMPLETE
            self.inspection_completed_at = timezone.now()
            self.inspected_by_id = inspector_id

            # Determine overall inspection status based on lines
            lines = self.lines.all()
            if all(line.inspection_result == InspectionResult.ACCEPT for line in lines):
                self.inspection_status = InspectionStatus.PASSED
            elif any(line.inspection_result == InspectionResult.REJECT for line in lines):
                self.inspection_status = InspectionStatus.FAILED
            else:
                self.inspection_status = InspectionStatus.CONDITIONAL

            self.save(update_fields=[
                'status', 'inspection_status',
                'inspection_completed_at', 'inspected_by_id'
            ])
            return True
        return False

    def post_to_inventory(self, user):
        """Post GRN to inventory - creates inventory transactions"""
        if self.status == GRNStatus.INSPECTION_COMPLETE:
            self.status = GRNStatus.POSTED
            self.posted_at = timezone.now()
            self.posted_by = user
            self.save(update_fields=['status', 'posted_at', 'posted_by'])

            # Update PO receipt status
            self.purchase_order.update_receipt_status()
            return True
        return False

    @property
    def total_received_value(self):
        """Calculate total value of received goods"""
        return sum(line.total_value for line in self.lines.all())

    @classmethod
    def generate_grn_number(cls):
        """Generate next GRN number"""
        year = timezone.now().year
        prefix = f'GRN-{year}-'
        last_grn = cls.all_objects.filter(
            grn_number__startswith=prefix
        ).order_by('-grn_number').first()

        if last_grn:
            last_num = int(last_grn.grn_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class GRNLine(AuditMixin):
    """
    Individual line item in a GRN.
    """
    grn = models.ForeignKey(
        GoodsReceiptNote,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    po_line = models.ForeignKey(
        'purchasing.PurchaseOrderLine',
        on_delete=models.PROTECT,
        related_name='grn_lines'
    )
    line_number = models.PositiveIntegerField()

    # Item Reference
    item_id = models.BigIntegerField(db_index=True)
    item_code = models.CharField(max_length=50)
    description = models.CharField(max_length=500)

    # Quantities
    quantity_ordered = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Quantity ordered on PO"
    )
    quantity_received = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Quantity actually received"
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
    uom = models.CharField(max_length=20, default='EA')

    # Pricing
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Storage Location
    storage_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Final storage location"
    )
    storage_bin = models.CharField(max_length=50, blank=True)

    # Serial/Batch Tracking
    serial_numbers = models.JSONField(
        default=list,
        blank=True,
        help_text="List of serial numbers if serialized"
    )
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    manufacturer_batch = models.CharField(max_length=100, blank=True)

    # Inspection
    requires_inspection = models.BooleanField(default=True)
    inspection_result = models.CharField(
        max_length=25,
        choices=InspectionResult.CHOICES,
        blank=True
    )
    inspection_notes = models.TextField(blank=True)

    # Damage
    is_damaged = models.BooleanField(default=False)
    damage_description = models.TextField(blank=True)
    damage_photos = models.JSONField(default=list, blank=True)

    # QR Code
    qcode_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="QR Code reference for tracking"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_grn_line'
        verbose_name = 'GRN Line'
        verbose_name_plural = 'GRN Lines'
        ordering = ['grn', 'line_number']
        unique_together = [['grn', 'line_number']]
        indexes = [
            models.Index(fields=['item_id'], name='ix_grnline_item'),
        ]

    def __str__(self):
        return f"{self.grn.grn_number} Line {self.line_number}"

    def save(self, *args, **kwargs):
        # Calculate total value based on accepted quantity
        self.total_value = self.quantity_accepted * self.unit_price
        super().save(*args, **kwargs)

    def accept_all(self):
        """Accept all received quantity"""
        self.quantity_accepted = self.quantity_received
        self.quantity_rejected = 0
        self.inspection_result = InspectionResult.ACCEPT
        self.save()

    def reject_all(self, reason=''):
        """Reject all received quantity"""
        self.quantity_accepted = 0
        self.quantity_rejected = self.quantity_received
        self.inspection_result = InspectionResult.REJECT
        self.inspection_notes = reason
        self.save()

    def partial_accept(self, accepted_qty, rejected_qty, reason=''):
        """Partially accept received quantity"""
        self.quantity_accepted = accepted_qty
        self.quantity_rejected = rejected_qty
        self.inspection_result = InspectionResult.ACCEPT_WITH_DEVIATION
        self.inspection_notes = reason
        self.save()


class QualityInspection(AuditMixin):
    """
    Detailed quality inspection record for GRN lines.
    """
    grn_line = models.ForeignKey(
        GRNLine,
        on_delete=models.CASCADE,
        related_name='inspections'
    )

    # Inspector
    inspector_id = models.BigIntegerField(
        db_index=True,
        help_text="Employee ID of inspector"
    )
    inspection_date = models.DateTimeField(default=timezone.now)

    # Inspection Criteria
    parameter = models.CharField(
        max_length=200,
        help_text="What is being inspected"
    )
    specification = models.CharField(
        max_length=200,
        help_text="Required specification"
    )
    actual_value = models.CharField(
        max_length=200,
        help_text="Actual measured/observed value"
    )
    tolerance = models.CharField(max_length=100, blank=True)

    # Result
    result = models.CharField(
        max_length=10,
        choices=[
            ('PASS', 'Pass'),
            ('FAIL', 'Fail'),
            ('WARN', 'Warning'),
        ]
    )
    is_critical = models.BooleanField(
        default=False,
        help_text="Is this a critical inspection point"
    )

    # Equipment Used
    measurement_tool = models.CharField(max_length=200, blank=True)
    tool_calibration_id = models.CharField(max_length=100, blank=True)

    # Evidence
    photo_path = models.CharField(max_length=500, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_quality_inspection'
        verbose_name = 'Quality Inspection'
        verbose_name_plural = 'Quality Inspections'
        ordering = ['grn_line', 'inspection_date']

    def __str__(self):
        return f"{self.grn_line} - {self.parameter}: {self.result}"
