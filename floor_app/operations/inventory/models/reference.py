"""
Reference/Lookup Tables for Inventory Management

These are the foundational tables that provide controlled vocabularies
for conditions, ownership, units of measure, and item categories.
"""

from django.db import models
from floor_app.mixins import AuditMixin, SoftDeleteMixin


class ConditionType(models.Model):
    """
    Defines the physical condition of inventory items.

    Examples:
    - NEW: Brand new purchased stock
    - RECLAIM_AS_NEW: Reclaimed from unused bits, physically as good as new
    - USED_REGRINDABLE: From used bits, can be reground
    - REGROUND: Already reground and qualified
    - UNDER_INSPECTION: Being evaluated
    - SCRAP: End of life
    """
    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Unique code identifier (e.g., NEW, RECLAIM_AS_NEW)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0, help_text="Display order in UI")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_condition_type"
        verbose_name = "Condition Type"
        verbose_name_plural = "Condition Types"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class OwnershipType(models.Model):
    """
    Defines who owns the inventory.

    Examples:
    - ARDT: Company-owned stock
    - ENO: Internal reclaimed from obsolete/unused bits
    - LSTK: Long-term stock keeping partner
    - JV_PARTNER: Joint venture partner owned
    - CUSTOMER_ARAMCO: Customer-owned consignment stock
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code identifier (e.g., ARDT, ENO, CUSTOMER_ARAMCO)"
    )
    name = models.CharField(max_length=100)
    is_internal = models.BooleanField(
        default=False,
        help_text="True if owned by ARDT or internal bucket (ENO)"
    )
    is_consignment = models.BooleanField(
        default=False,
        help_text="True if customer/partner consignment stock"
    )
    description = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_ownership_type"
        verbose_name = "Ownership Type"
        verbose_name_plural = "Ownership Types"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class UnitOfMeasure(models.Model):
    """
    Standard units of measure for inventory tracking.

    Examples: PC (piece), KG (kilogram), L (liter), SET, BOX, PAIR
    """

    UOM_TYPE_CHOICES = (
        ('COUNT', 'Count/Quantity'),
        ('WEIGHT', 'Weight'),
        ('VOLUME', 'Volume'),
        ('LENGTH', 'Length'),
        ('AREA', 'Area'),
        ('TIME', 'Time'),
        ('OTHER', 'Other'),
    )

    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Short code (e.g., PC, KG, L)"
    )
    name = models.CharField(max_length=50)
    uom_type = models.CharField(
        max_length=20,
        choices=UOM_TYPE_CHOICES,
        default='COUNT'
    )
    # Conversion to base unit (optional, for future inventory calculations)
    base_uom = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='derived_units',
        help_text="Base unit for conversion (e.g., grams for kg)"
    )
    conversion_factor = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Multiply by this to convert to base unit"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_unit_of_measure"
        verbose_name = "Unit of Measure"
        verbose_name_plural = "Units of Measure"
        ordering = ['uom_type', 'code']

    def __str__(self):
        return f"{self.code} ({self.name})"


class ItemCategory(AuditMixin, SoftDeleteMixin):
    """
    Hierarchical categorization of inventory items.

    Examples:
    - BIT_FULL_ASSEMBLY (serialized=True): Complete PDC bits
    - BIT_HEAD: Bit head designs
    - BIT_BODY_NO_CUTTERS: Bit body without cutters
    - CUTTER: PDC cutters (non-serialized)
    - CONSUMABLE: Brazing powders, flux, etc.
    - TOOL: Impact wrenches, cameras, etc.
    - PPE: Personal protective equipment
    - SPARE_PART: Spare parts
    - SERVICE: Service items
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique category code (e.g., BIT_FULL_ASSEMBLY)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")

    # Hierarchy support
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="Parent category for hierarchical organization"
    )

    # Behavior flags
    is_serialized = models.BooleanField(
        default=False,
        help_text="True if items in this category are tracked individually by serial number"
    )
    is_bit_related = models.BooleanField(
        default=False,
        help_text="True if this category is related to bit designs"
    )

    # Display
    icon = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Icon name for UI display (optional)"
    )
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_item_category"
        verbose_name = "Item Category"
        verbose_name_plural = "Item Categories"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_path(self):
        """Returns the full category path (e.g., 'MATERIALS > CONSUMABLES > BRAZING')"""
        path = [self.name]
        parent = self.parent_category
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent_category
        return " > ".join(path)
