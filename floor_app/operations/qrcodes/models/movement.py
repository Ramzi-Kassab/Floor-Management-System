"""
Inventory movement tracking models.

Implements WHO/WHAT/WHEN/WHERE/WHY for all item movements,
including BOM material pickup workflow.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class MovementType:
    """Types of inventory movements."""
    TRANSFER = 'TRANSFER'
    RECEIPT = 'RECEIPT'
    ISSUE = 'ISSUE'
    BOM_PICKUP = 'BOM_PICKUP'
    BOM_RETURN = 'BOM_RETURN'
    ADJUSTMENT = 'ADJUSTMENT'
    SCRAP = 'SCRAP'
    RETURN_TO_VENDOR = 'RETURN_TO_VENDOR'
    INTERNAL_USE = 'INTERNAL_USE'

    CHOICES = (
        (TRANSFER, 'Location Transfer'),
        (RECEIPT, 'Receipt from Vendor'),
        (ISSUE, 'Issue to Production'),
        (BOM_PICKUP, 'BOM Material Pickup'),
        (BOM_RETURN, 'BOM Material Return'),
        (ADJUSTMENT, 'Inventory Adjustment'),
        (SCRAP, 'Scrap/Disposal'),
        (RETURN_TO_VENDOR, 'Return to Vendor'),
        (INTERNAL_USE, 'Internal Use'),
    )


class MovementLogManager(models.Manager):
    """Custom manager for MovementLog."""

    def for_serial_unit(self, serial_unit_id):
        """Get movements for a specific serial unit."""
        return self.filter(serial_unit_id=serial_unit_id).order_by('-moved_at')

    def for_item(self, item_id):
        """Get movements for a specific item."""
        return self.filter(item_id=item_id).order_by('-moved_at')

    def for_job_card(self, job_card_id):
        """Get movements related to a job card."""
        return self.filter(job_card_id=job_card_id).order_by('-moved_at')

    def bom_pickups(self):
        """Get BOM material pickups."""
        return self.filter(movement_type=MovementType.BOM_PICKUP)

    def bom_returns(self):
        """Get BOM material returns."""
        return self.filter(movement_type=MovementType.BOM_RETURN)

    def recent(self, hours=24):
        """Get recent movements."""
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        return self.filter(moved_at__gte=cutoff)


class MovementLog(AuditMixin):
    """
    Comprehensive inventory movement log.

    Tracks WHO moved WHAT, WHEN, from WHERE to WHERE, and WHY.

    Integrates with QR scanning for both origin and destination tracking.
    """

    # WHAT - Item identification
    # Can be serialized (SerialUnit) or non-serialized (Item + quantity)
    serial_unit_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Serial unit ID (for serialized items)"
    )

    item_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Item ID (for non-serialized items)"
    )

    # Cached item info for reporting
    item_sku = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Item SKU (cached)"
    )
    item_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Item name (cached)"
    )

    # Quantity (for non-serialized items)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=1,
        help_text="Quantity moved (1 for serialized items)"
    )

    uom_code = models.CharField(
        max_length=20,
        blank=True,
        default="EA",
        help_text="Unit of measure code"
    )

    # WHERE - Location tracking
    from_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Source location ID"
    )
    from_location_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Source location code (cached)"
    )
    from_location_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Source location name (cached)"
    )

    to_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Destination location ID"
    )
    to_location_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Destination location code (cached)"
    )
    to_location_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Destination location name (cached)"
    )

    # Container tracking (for bin/box movements)
    from_container_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Source container ID"
    )
    to_container_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Destination container ID"
    )

    # WHO - Person tracking
    moved_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_movements',
        help_text="User who performed movement"
    )
    moved_by_employee_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="HR Employee ID"
    )
    moved_by_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Employee name (cached)"
    )

    # WHEN - Timestamp
    moved_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When movement occurred"
    )

    # WHY - Reason and context
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.CHOICES,
        db_index=True,
        help_text="Type of movement"
    )

    reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for movement"
    )

    # Job Card context (for BOM pickups and production)
    job_card_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Related job card ID"
    )
    job_card_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Job card number (cached)"
    )

    # BOM context (for material pickups)
    bom_header_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="BOM header ID"
    )
    bom_line_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="BOM line ID"
    )

    # Batch order context
    batch_order_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Batch order ID"
    )

    # QR Scan tracking
    source_scan_log_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ScanLog ID for source item scan"
    )
    destination_scan_log_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ScanLog ID for destination location scan"
    )

    # Cost tracking
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Unit cost at time of movement"
    )
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Total cost of movement"
    )

    # Reference documents
    reference_document = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="External reference (PO, SO, etc.)"
    )

    # Verification
    verified = models.BooleanField(
        default=False,
        help_text="Has movement been verified?"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_movements',
        help_text="User who verified"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When verified"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes"
    )

    objects = MovementLogManager()

    class Meta:
        db_table = 'qrcode_movement_log'
        verbose_name = 'Movement Log'
        verbose_name_plural = 'Movement Logs'
        ordering = ['-moved_at']
        indexes = [
            models.Index(fields=['-moved_at'], name='ix_movlog_moved_at'),
            models.Index(fields=['serial_unit_id'], name='ix_movlog_serial'),
            models.Index(fields=['item_id'], name='ix_movlog_item'),
            models.Index(fields=['job_card_id'], name='ix_movlog_jobcard'),
            models.Index(fields=['bom_line_id'], name='ix_movlog_bomline'),
            models.Index(fields=['from_location_id'], name='ix_movlog_from'),
            models.Index(fields=['to_location_id'], name='ix_movlog_to'),
            models.Index(fields=['movement_type'], name='ix_movlog_type'),
            models.Index(fields=['moved_by_employee_id'], name='ix_movlog_employee'),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item_name or self.item_sku} at {self.moved_at}"

    @classmethod
    def create_bom_pickup(cls, bom_line, job_card, quantity, user=None,
                          employee_id=None, employee_name="", notes=""):
        """
        Create a BOM material pickup record.

        This is called when materials are picked from stock for a job card.

        Args:
            bom_line: BOM line being fulfilled
            job_card: Job card requiring materials
            quantity: Quantity being picked
            user: User performing pickup
            employee_id: HR Employee ID
            employee_name: Employee name
            notes: Optional notes

        Returns:
            MovementLog instance
        """
        log = cls(
            movement_type=MovementType.BOM_PICKUP,
            item_id=bom_line.item_id if hasattr(bom_line, 'item_id') else None,
            item_sku=bom_line.item.sku if hasattr(bom_line, 'item') else "",
            item_name=bom_line.item.name if hasattr(bom_line, 'item') else "",
            quantity=quantity,
            uom_code=bom_line.uom.code if hasattr(bom_line, 'uom') else "EA",
            job_card_id=job_card.pk if hasattr(job_card, 'pk') else None,
            job_card_number=job_card.job_card_number if hasattr(job_card, 'job_card_number') else "",
            bom_header_id=bom_line.header_id if hasattr(bom_line, 'header_id') else None,
            bom_line_id=bom_line.pk if hasattr(bom_line, 'pk') else None,
            moved_by_user=user,
            moved_by_employee_id=employee_id,
            moved_by_name=employee_name,
            reason=f"BOM material pickup for job card",
            notes=notes,
        )
        log.save()
        return log

    @classmethod
    def create_bom_return(cls, bom_line, job_card, quantity, user=None,
                          employee_id=None, employee_name="", notes=""):
        """
        Create a BOM material return record.

        This is called when unused materials are returned to stock.
        """
        log = cls(
            movement_type=MovementType.BOM_RETURN,
            item_id=bom_line.item_id if hasattr(bom_line, 'item_id') else None,
            item_sku=bom_line.item.sku if hasattr(bom_line, 'item') else "",
            item_name=bom_line.item.name if hasattr(bom_line, 'item') else "",
            quantity=quantity,
            uom_code=bom_line.uom.code if hasattr(bom_line, 'uom') else "EA",
            job_card_id=job_card.pk if hasattr(job_card, 'pk') else None,
            job_card_number=job_card.job_card_number if hasattr(job_card, 'job_card_number') else "",
            bom_header_id=bom_line.header_id if hasattr(bom_line, 'header_id') else None,
            bom_line_id=bom_line.pk if hasattr(bom_line, 'pk') else None,
            moved_by_user=user,
            moved_by_employee_id=employee_id,
            moved_by_name=employee_name,
            reason=f"BOM material return - excess/unused",
            notes=notes,
        )
        log.save()
        return log


class ContainerType:
    """Types of containers."""
    BIT_BOX = 'BIT_BOX'
    BIN = 'BIN'
    PALLET = 'PALLET'
    RACK = 'RACK'
    TOTE = 'TOTE'
    CRATE = 'CRATE'
    OTHER = 'OTHER'

    CHOICES = (
        (BIT_BOX, 'Bit Box'),
        (BIN, 'Bin'),
        (PALLET, 'Pallet'),
        (RACK, 'Rack'),
        (TOTE, 'Tote'),
        (CRATE, 'Crate'),
        (OTHER, 'Other'),
    )


class ContainerStatus:
    """Status of containers."""
    AVAILABLE = 'AVAILABLE'
    IN_USE = 'IN_USE'
    IN_TRANSIT = 'IN_TRANSIT'
    DAMAGED = 'DAMAGED'
    RETIRED = 'RETIRED'

    CHOICES = (
        (AVAILABLE, 'Available'),
        (IN_USE, 'In Use'),
        (IN_TRANSIT, 'In Transit'),
        (DAMAGED, 'Damaged'),
        (RETIRED, 'Retired'),
    )


class ContainerManager(models.Manager):
    """Custom manager for Container."""

    def available(self):
        """Get available containers."""
        return self.filter(status=ContainerStatus.AVAILABLE, is_deleted=False)

    def in_use(self):
        """Get containers in use."""
        return self.filter(status=ContainerStatus.IN_USE, is_deleted=False)

    def at_location(self, location_id):
        """Get containers at a specific location."""
        return self.filter(location_id=location_id, is_deleted=False)

    def bit_boxes(self):
        """Get bit box containers."""
        return self.filter(container_type=ContainerType.BIT_BOX, is_deleted=False)


class Container(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Physical container for inventory items (Bit Boxes, Bins, Pallets, etc.).

    QR-enabled for scanning and movement tracking.
    """

    # Identification
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique container code"
    )

    name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Container name or label"
    )

    # Classification
    container_type = models.CharField(
        max_length=20,
        choices=ContainerType.CHOICES,
        default=ContainerType.BIT_BOX,
        db_index=True,
        help_text="Type of container"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=ContainerStatus.CHOICES,
        default=ContainerStatus.AVAILABLE,
        db_index=True,
        help_text="Current status"
    )

    # Location
    location_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Current location ID"
    )
    location_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Location code (cached)"
    )
    location_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Location name (cached)"
    )

    # Capacity
    max_capacity = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of items"
    )

    current_count = models.IntegerField(
        default=0,
        help_text="Current number of items"
    )

    # Physical attributes
    weight_empty_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Empty weight in kg"
    )

    weight_max_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum loaded weight in kg"
    )

    length_cm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Length in cm"
    )

    width_cm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Width in cm"
    )

    height_cm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Height in cm"
    )

    # Assigned to specific use
    dedicated_to_item_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="If dedicated to a specific item type"
    )

    dedicated_to_customer = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="If dedicated to a specific customer"
    )

    # QR Code reference
    qcode_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="QCode ID for this container"
    )

    # Tracking
    last_movement_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time container was moved"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes"
    )

    objects = ContainerManager()

    class Meta:
        db_table = 'qrcode_container'
        verbose_name = 'Container'
        verbose_name_plural = 'Containers'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code'], name='ix_container_code'),
            models.Index(fields=['container_type'], name='ix_container_type'),
            models.Index(fields=['status'], name='ix_container_status'),
            models.Index(fields=['location_id'], name='ix_container_location'),
            models.Index(fields=['qcode_id'], name='ix_container_qcode'),
        ]

    def __str__(self):
        return f"{self.code} ({self.get_container_type_display()})"

    @property
    def is_empty(self):
        """Check if container is empty."""
        return self.current_count == 0

    @property
    def is_full(self):
        """Check if container is at capacity."""
        if not self.max_capacity:
            return False
        return self.current_count >= self.max_capacity

    @property
    def available_space(self):
        """Get available space in container."""
        if not self.max_capacity:
            return None
        return max(0, self.max_capacity - self.current_count)

    def add_item(self):
        """Add one item to container."""
        self.current_count += 1
        if self.current_count > 0:
            self.status = ContainerStatus.IN_USE
        self.save(update_fields=['current_count', 'status'])

    def remove_item(self):
        """Remove one item from container."""
        if self.current_count > 0:
            self.current_count -= 1
        if self.current_count == 0:
            self.status = ContainerStatus.AVAILABLE
        self.save(update_fields=['current_count', 'status'])

    def move_to_location(self, location_id, location_code="", location_name=""):
        """Move container to a new location."""
        self.location_id = location_id
        self.location_code = location_code
        self.location_name = location_name
        self.last_movement_at = timezone.now()
        self.status = ContainerStatus.IN_TRANSIT if location_id else self.status
        self.save()
