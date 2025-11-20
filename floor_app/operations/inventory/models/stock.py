"""
Physical Stock Layer - Real Units, Locations, Conditions, and Ownership

This layer tracks:
- Locations (warehouses, bins, rigs, customer sites)
- SerialUnit: Individual serialized items (PDC bits, expensive tools)
- InventoryStock: Non-serialized items tracked by quantity
- SerialUnitMATHistory: MAT revision changes for serialized bits
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class Location(AuditMixin, SoftDeleteMixin):
    """
    Inventory location hierarchy (warehouses, bins, rigs, customer sites).

    Supports hierarchical structure: Warehouse > Zone > Bin
    """

    LOCATION_TYPE_CHOICES = (
        ('WAREHOUSE', 'Warehouse'),
        ('ZONE', 'Warehouse Zone'),
        ('BIN', 'Storage Bin'),
        ('RIG', 'Drilling Rig'),
        ('CUSTOMER_SITE', 'Customer Site'),
        ('REPAIR_SHOP', 'Repair Shop'),
        ('INSPECTION', 'Inspection Area'),
        ('QUARANTINE', 'Quarantine Area'),
        ('TRANSIT', 'In Transit'),
        ('SCRAP', 'Scrap/Disposal'),
        ('OTHER', 'Other'),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Location code (e.g., WH-01, BIN-A1-01)"
    )
    name = models.CharField(max_length=100)
    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_TYPE_CHOICES,
        default='BIN'
    )

    # Hierarchy
    parent_location = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='child_locations',
        help_text="Parent location for hierarchical organization"
    )

    # Physical address (optional)
    address = models.TextField(blank=True, default="")
    gps_coordinates = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="GPS coordinates (lat,long)"
    )

    # Constraints
    max_capacity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum storage capacity (units or volume)"
    )
    capacity_uom = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='capacity_locations',
        help_text="Unit of measure for capacity"
    )

    is_active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_location"
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code'], name='ix_loc_code'),
            models.Index(fields=['location_type', 'is_active'], name='ix_loc_type_active'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_path(self):
        """Returns the full location path (e.g., 'WH-01 > ZONE-A > BIN-A1-01')"""
        path = [self.code]
        parent = self.parent_location
        while parent:
            path.insert(0, parent.code)
            parent = parent.parent_location
        return " > ".join(path)


class SerialUnit(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Individual serialized inventory unit (e.g., PDC bit, expensive tool).

    Each physical unit has its own serial number and lifecycle.
    Tracks current MAT revision (can change after retrofit).
    """

    STATUS_CHOICES = (
        ('IN_STOCK', 'In Stock'),
        ('RESERVED', 'Reserved'),
        ('AT_RIG', 'At Drilling Rig'),
        ('UNDER_REPAIR', 'Under Repair'),
        ('UNDER_INSPECTION', 'Under Inspection'),
        ('IN_TRANSIT', 'In Transit'),
        ('SCRAPPED', 'Scrapped'),
        ('SOLD', 'Sold'),
        ('LOST', 'Lost'),
    )

    # Core identification
    item = models.ForeignKey(
        'Item',
        on_delete=models.PROTECT,
        related_name='serial_units',
        help_text="Item master record this unit belongs to"
    )
    serial_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique serial number for this physical unit"
    )

    # Current MAT version (can differ from item's design after retrofit)
    current_mat = models.ForeignKey(
        'engineering.BitDesignRevision',  # ⚠️ Model moved to engineering app
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='serial_units',
        help_text="Current MAT revision (may differ from Item after retrofit)"
    )

    # Current state
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='serial_units',
        help_text="Current physical location"
    )
    condition = models.ForeignKey(
        'ConditionType',
        on_delete=models.PROTECT,
        related_name='serial_units',
        help_text="Current physical condition"
    )
    ownership = models.ForeignKey(
        'OwnershipType',
        on_delete=models.PROTECT,
        related_name='serial_units',
        help_text="Current ownership (ARDT, ENO, customer, etc.)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_STOCK',
        db_index=True
    )

    # Lifecycle dates
    manufacture_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of manufacture/assembly"
    )
    received_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date received into inventory"
    )
    last_run_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last drilling run"
    )
    warranty_expiry = models.DateField(
        null=True,
        blank=True,
        help_text="Warranty expiration date"
    )

    # Usage tracking (for PDC bits)
    total_run_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total drilling hours"
    )
    total_footage_drilled = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total footage drilled (feet or meters)"
    )
    run_count = models.IntegerField(
        default=0,
        help_text="Number of times this bit has been run"
    )

    # Cost tracking
    acquisition_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Original acquisition cost"
    )
    current_book_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Current book value after depreciation"
    )

    # Customer/Job tracking
    current_customer = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Current customer using this unit"
    )
    current_job_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Current job card or work order reference"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_serial_unit"
        verbose_name = "Serial Unit"
        verbose_name_plural = "Serial Units"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['serial_number'], name='ix_su_serial'),
            models.Index(fields=['item', 'status'], name='ix_su_item_status'),
            models.Index(fields=['current_mat'], name='ix_su_current_mat'),
            models.Index(fields=['location', 'status'], name='ix_su_loc_status'),
            models.Index(fields=['ownership', 'condition'], name='ix_su_owner_cond'),
            models.Index(fields=['status'], name='ix_su_status'),
        ]

    def __str__(self):
        return f"{self.serial_number} ({self.item.sku})"

    def clean(self):
        """Validate serial unit data."""
        super().clean()

        # Item must be serialized
        if self.item and not self.item.is_serialized:
            raise ValidationError({
                'item': "Serial units can only be created for serialized item categories."
            })

        # If item is bit-related and no current_mat, inherit from item
        if self.item and self.item.bit_design_revision and not self.current_mat:
            self.current_mat = self.item.bit_design_revision

    @property
    def mat_number(self):
        """Get current MAT number for this unit."""
        if self.current_mat:
            return self.current_mat.mat_number
        return None

    @property
    def is_available(self):
        """Check if unit is available for dispatch."""
        return self.status == 'IN_STOCK'

    def change_mat(self, new_mat, reason='RETROFIT', user=None, notes=''):
        """
        Change the MAT revision for this unit (e.g., after retrofit).

        Records the change in SerialUnitMATHistory.
        """
        old_mat = self.current_mat
        if old_mat == new_mat:
            return  # No change needed

        # Record history
        SerialUnitMATHistory.objects.create(
            serial_unit=self,
            old_mat=old_mat,
            new_mat=new_mat,
            reason=reason,
            changed_by=user,
            notes=notes
        )

        # Update current MAT
        self.current_mat = new_mat
        self.save(update_fields=['current_mat', 'updated_at'])


class SerialUnitMATHistory(models.Model):
    """
    Audit trail for MAT revision changes on serialized units.

    Tracks when a bit's design configuration changes due to:
    - Retrofit
    - Correction
    - Upgrade
    - Testing with different configuration
    """

    REASON_CHOICES = (
        ('RETROFIT', 'Retrofit'),
        ('CORRECTION', 'Data Correction'),
        ('UPGRADE', 'Design Upgrade'),
        ('DOWNGRADE', 'Design Downgrade'),
        ('TESTING', 'Testing Configuration'),
        ('OTHER', 'Other'),
    )

    serial_unit = models.ForeignKey(
        SerialUnit,
        on_delete=models.CASCADE,
        related_name='mat_history',
        help_text="Serial unit that was modified"
    )
    old_mat = models.ForeignKey(
        'engineering.BitDesignRevision',  # ⚠️ Model moved to engineering app
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_as_old',
        help_text="Previous MAT revision (null if first assignment)"
    )
    new_mat = models.ForeignKey(
        'engineering.BitDesignRevision',  # ⚠️ Model moved to engineering app
        on_delete=models.PROTECT,
        related_name='history_as_new',
        help_text="New MAT revision"
    )
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        default='RETROFIT'
    )
    changed_at = models.DateTimeField(default=timezone.now)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mat_changes'
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_serial_unit_mat_history"
        verbose_name = "Serial Unit MAT History"
        verbose_name_plural = "Serial Unit MAT Histories"
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['serial_unit', '-changed_at'], name='ix_sumh_unit_date'),
        ]

    def __str__(self):
        old = self.old_mat.mat_number if self.old_mat else "None"
        return f"{self.serial_unit.serial_number}: {old} -> {self.new_mat.mat_number}"


class InventoryStock(AuditMixin):
    """
    Non-serialized inventory stock tracked by quantity.

    Key dimension: item + location + condition + ownership
    Each unique combination has its own quantity record.

    Examples:
    - 50 NEW cutters owned by ARDT in warehouse WH-01
    - 25 RECLAIM_AS_NEW cutters owned by ENO in warehouse WH-01
    - 100 kg brazing powder owned by ARDT in bin BIN-A1-01
    """

    # Dimensions (unique combination)
    item = models.ForeignKey(
        'Item',
        on_delete=models.PROTECT,
        related_name='inventory_stocks',
        help_text="Item master record"
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='inventory_stocks',
        help_text="Storage location"
    )
    condition = models.ForeignKey(
        'ConditionType',
        on_delete=models.PROTECT,
        related_name='inventory_stocks',
        help_text="Physical condition"
    )
    ownership = models.ForeignKey(
        'OwnershipType',
        on_delete=models.PROTECT,
        related_name='inventory_stocks',
        help_text="Ownership (ARDT, ENO, customer, etc.)"
    )

    # Quantities
    quantity_on_hand = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text="Total quantity physically present"
    )
    quantity_reserved = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text="Quantity reserved for orders/jobs"
    )
    quantity_on_order = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text="Quantity on purchase/production orders"
    )

    # Reorder settings (can override item-level defaults)
    reorder_point = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Location-specific reorder point"
    )
    safety_stock = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Location-specific safety stock"
    )

    # Cost tracking
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Average unit cost at this location"
    )

    # Audit
    last_counted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last physical inventory count date"
    )
    last_movement_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last stock movement date"
    )

    class Meta:
        db_table = "inventory_stock"
        verbose_name = "Inventory Stock"
        verbose_name_plural = "Inventory Stocks"
        ordering = ['item__sku', 'location__code']
        constraints = [
            models.UniqueConstraint(
                fields=['item', 'location', 'condition', 'ownership'],
                name='uq_stock_dimension'
            ),
            models.CheckConstraint(
                check=models.Q(quantity_on_hand__gte=0),
                name='ck_stock_qty_positive'
            ),
            models.CheckConstraint(
                check=models.Q(quantity_reserved__gte=0),
                name='ck_stock_reserved_positive'
            ),
        ]
        indexes = [
            models.Index(fields=['item', 'location'], name='ix_stock_item_loc'),
            models.Index(fields=['location', 'condition'], name='ix_stock_loc_cond'),
            models.Index(fields=['ownership'], name='ix_stock_ownership'),
        ]

    def __str__(self):
        loc = self.location.code if self.location else "NO_LOC"
        return f"{self.item.sku} @ {loc} [{self.condition.code}/{self.ownership.code}]: {self.quantity_on_hand}"

    @property
    def quantity_available(self):
        """Quantity available for use (on hand minus reserved)."""
        return self.quantity_on_hand - self.quantity_reserved

    @property
    def total_value(self):
        """Total value of this stock (quantity * unit cost)."""
        if self.unit_cost:
            return self.quantity_on_hand * self.unit_cost
        return None

    @property
    def is_below_reorder_point(self):
        """Check if stock is below reorder threshold."""
        threshold = self.reorder_point or (self.item.reorder_point if self.item else 0)
        return self.quantity_available <= threshold

    def adjust_quantity(self, qty_change, user=None):
        """
        Adjust quantity on hand.

        Args:
            qty_change: Positive for increase, negative for decrease
            user: User performing the adjustment
        """
        new_qty = self.quantity_on_hand + qty_change
        if new_qty < 0:
            raise ValidationError(
                f"Cannot reduce quantity below 0. Current: {self.quantity_on_hand}, Change: {qty_change}"
            )

        self.quantity_on_hand = new_qty
        self.last_movement_at = timezone.now()
        self.save(update_fields=['quantity_on_hand', 'last_movement_at', 'updated_at'])

    def reserve(self, qty, user=None):
        """
        Reserve quantity for a job/order.

        Args:
            qty: Quantity to reserve (positive number)
        """
        if qty > self.quantity_available:
            raise ValidationError(
                f"Cannot reserve {qty}. Only {self.quantity_available} available."
            )

        self.quantity_reserved += qty
        self.save(update_fields=['quantity_reserved', 'updated_at'])

    def release_reservation(self, qty):
        """
        Release reserved quantity back to available.

        Args:
            qty: Quantity to release (positive number)
        """
        if qty > self.quantity_reserved:
            raise ValidationError(
                f"Cannot release {qty}. Only {self.quantity_reserved} reserved."
            )

        self.quantity_reserved -= qty
        self.save(update_fields=['quantity_reserved', 'updated_at'])
