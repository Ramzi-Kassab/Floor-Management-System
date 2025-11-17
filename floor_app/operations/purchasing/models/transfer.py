"""
Internal Transfer Orders Models

Manages movement of inventory between warehouses and locations.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class TransferStatus:
    """Transfer Order status states"""
    DRAFT = 'DRAFT'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    IN_TRANSIT = 'IN_TRANSIT'
    PARTIALLY_RECEIVED = 'PARTIALLY_RECEIVED'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

    CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_APPROVAL, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (IN_TRANSIT, 'In Transit'),
        (PARTIALLY_RECEIVED, 'Partially Received'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]


class TransferType:
    """Types of internal transfers"""
    WAREHOUSE_TO_WAREHOUSE = 'W2W'
    WAREHOUSE_TO_SHOP = 'W2S'
    SHOP_TO_WAREHOUSE = 'S2W'
    LOCATION_TO_LOCATION = 'L2L'
    PRODUCTION_ISSUE = 'PROD'
    PRODUCTION_RETURN = 'PRET'
    QA_HOLD = 'QAH'
    QA_RELEASE = 'QAR'

    CHOICES = [
        (WAREHOUSE_TO_WAREHOUSE, 'Warehouse to Warehouse'),
        (WAREHOUSE_TO_SHOP, 'Warehouse to Shop Floor'),
        (SHOP_TO_WAREHOUSE, 'Shop Floor to Warehouse'),
        (LOCATION_TO_LOCATION, 'Location to Location'),
        (PRODUCTION_ISSUE, 'Production Issue'),
        (PRODUCTION_RETURN, 'Production Return'),
        (QA_HOLD, 'QA Hold'),
        (QA_RELEASE, 'QA Release'),
    ]


class TransferPriority:
    """Transfer priority levels"""
    LOW = 'LOW'
    NORMAL = 'NORMAL'
    HIGH = 'HIGH'
    URGENT = 'URGENT'

    CHOICES = [
        (LOW, 'Low'),
        (NORMAL, 'Normal'),
        (HIGH, 'High'),
        (URGENT, 'Urgent'),
    ]


class InternalTransferOrder(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Internal Transfer Order for moving inventory between locations.
    """
    # Identification
    transfer_number = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        help_text="Auto-generated transfer number"
    )
    transfer_type = models.CharField(
        max_length=10,
        choices=TransferType.CHOICES,
        default=TransferType.WAREHOUSE_TO_WAREHOUSE
    )
    status = models.CharField(
        max_length=20,
        choices=TransferStatus.CHOICES,
        default=TransferStatus.DRAFT,
        db_index=True
    )
    priority = models.CharField(
        max_length=10,
        choices=TransferPriority.CHOICES,
        default=TransferPriority.NORMAL
    )

    # Source Location
    source_warehouse_id = models.BigIntegerField(
        db_index=True,
        help_text="Source Warehouse ID"
    )
    source_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Specific source location/bin"
    )
    source_location_name = models.CharField(max_length=200)

    # Destination Location
    destination_warehouse_id = models.BigIntegerField(
        db_index=True,
        help_text="Destination Warehouse ID"
    )
    destination_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Specific destination location/bin"
    )
    destination_location_name = models.CharField(max_length=200)

    # Requester
    requester_id = models.BigIntegerField(
        db_index=True,
        help_text="Employee ID of requester"
    )
    department_id = models.BigIntegerField(
        null=True,
        blank=True
    )

    # Dates
    request_date = models.DateField(default=timezone.now)
    required_by_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date by which transfer should be completed"
    )
    shipped_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)

    # Handler Information
    picker_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Employee who picked the items"
    )
    picked_at = models.DateTimeField(null=True, blank=True)

    shipped_by_id = models.BigIntegerField(null=True, blank=True)
    received_by_id = models.BigIntegerField(null=True, blank=True)

    # Approval
    approval_required = models.BooleanField(default=True)
    approver_id = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    # Reference
    job_card_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Related Job Card if production transfer"
    )
    bom_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Related BOM if production transfer"
    )

    # Totals
    total_items = models.IntegerField(default=0)
    total_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=0
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Inventory Transaction
    source_transaction_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Inventory transaction for source deduction"
    )
    destination_transaction_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Inventory transaction for destination addition"
    )

    reason = models.TextField(
        blank=True,
        help_text="Reason for transfer"
    )
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_transfer_order'
        verbose_name = 'Internal Transfer Order'
        verbose_name_plural = 'Internal Transfer Orders'
        ordering = ['-request_date', '-transfer_number']
        indexes = [
            models.Index(fields=['transfer_number'], name='ix_transfer_number'),
            models.Index(fields=['status'], name='ix_transfer_status'),
            models.Index(fields=['source_warehouse_id'], name='ix_transfer_src'),
            models.Index(fields=['destination_warehouse_id'], name='ix_transfer_dst'),
        ]

    def __str__(self):
        return f"{self.transfer_number} ({self.get_transfer_type_display()})"

    def approve(self, approver_id, notes=''):
        """Approve the transfer order"""
        if self.status == TransferStatus.PENDING_APPROVAL:
            self.status = TransferStatus.APPROVED
            self.approver_id = approver_id
            self.approved_at = timezone.now()
            self.approval_notes = notes
            self.save(update_fields=[
                'status', 'approver_id', 'approved_at', 'approval_notes'
            ])
            return True
        return False

    def start_picking(self, picker_id):
        """Start picking process"""
        if self.status == TransferStatus.APPROVED:
            self.picker_id = picker_id
            self.picked_at = timezone.now()
            self.save(update_fields=['picker_id', 'picked_at'])
            return True
        return False

    def ship(self, shipper_id):
        """Mark transfer as in transit"""
        if self.status == TransferStatus.APPROVED:
            self.status = TransferStatus.IN_TRANSIT
            self.shipped_by_id = shipper_id
            self.shipped_date = timezone.now()
            self.save(update_fields=['status', 'shipped_by_id', 'shipped_date'])
            return True
        return False

    def receive(self, receiver_id):
        """Mark transfer as received"""
        if self.status == TransferStatus.IN_TRANSIT:
            # Check if all lines are received
            lines = self.lines.all()
            if all(line.is_fully_received for line in lines):
                self.status = TransferStatus.COMPLETED
            else:
                self.status = TransferStatus.PARTIALLY_RECEIVED

            self.received_by_id = receiver_id
            self.received_date = timezone.now()
            self.save(update_fields=[
                'status', 'received_by_id', 'received_date'
            ])
            return True
        return False

    def calculate_totals(self):
        """Calculate totals from lines"""
        lines = self.lines.all()
        self.total_items = lines.count()
        self.total_quantity = sum(line.quantity_to_transfer for line in lines)
        self.total_value = sum(line.total_value for line in lines)
        self.save(update_fields=['total_items', 'total_quantity', 'total_value'])

    @classmethod
    def generate_transfer_number(cls):
        """Generate next transfer number"""
        year = timezone.now().year
        prefix = f'TO-{year}-'
        last_to = cls.all_objects.filter(
            transfer_number__startswith=prefix
        ).order_by('-transfer_number').first()

        if last_to:
            last_num = int(last_to.transfer_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"


class TransferOrderLine(AuditMixin):
    """
    Individual line item in a Transfer Order.
    """
    transfer_order = models.ForeignKey(
        InternalTransferOrder,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()

    # Item Reference
    item_id = models.BigIntegerField(db_index=True)
    item_code = models.CharField(max_length=50)
    description = models.CharField(max_length=500)

    # Quantities
    quantity_to_transfer = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    quantity_picked = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    quantity_shipped = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    quantity_received = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    uom = models.CharField(max_length=20, default='EA')

    # Value
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    # Serial/Batch
    serial_numbers = models.JSONField(
        default=list,
        blank=True,
        help_text="Serial numbers being transferred"
    )
    batch_number = models.CharField(max_length=50, blank=True)

    # Source Location Details
    source_bin = models.CharField(max_length=50, blank=True)

    # Destination Details
    destination_bin = models.CharField(max_length=50, blank=True)

    # Status
    is_fully_picked = models.BooleanField(default=False)
    is_fully_received = models.BooleanField(default=False)

    # QR Code
    qcode_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="QR Code for tracking"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'purchasing_transfer_line'
        verbose_name = 'Transfer Line'
        verbose_name_plural = 'Transfer Lines'
        ordering = ['transfer_order', 'line_number']
        unique_together = [['transfer_order', 'line_number']]
        indexes = [
            models.Index(fields=['item_id'], name='ix_transline_item'),
        ]

    def __str__(self):
        return f"{self.transfer_order.transfer_number} Line {self.line_number}"

    def save(self, *args, **kwargs):
        # Calculate total value
        self.total_value = self.quantity_to_transfer * self.unit_cost

        # Check if fully picked
        if self.quantity_picked >= self.quantity_to_transfer:
            self.is_fully_picked = True

        # Check if fully received
        if self.quantity_received >= self.quantity_to_transfer:
            self.is_fully_received = True

        super().save(*args, **kwargs)

    def pick(self, quantity):
        """Record quantity picked"""
        self.quantity_picked = quantity
        if self.quantity_picked >= self.quantity_to_transfer:
            self.is_fully_picked = True
        self.save(update_fields=['quantity_picked', 'is_fully_picked'])

    def receive(self, quantity):
        """Record quantity received"""
        self.quantity_received = quantity
        if self.quantity_received >= self.quantity_to_transfer:
            self.is_fully_received = True
        self.save(update_fields=['quantity_received', 'is_fully_received'])
