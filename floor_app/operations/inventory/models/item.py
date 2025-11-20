"""
Item Master - Universal Product Catalog

The central repository for all inventory items including:
- PDC bits (linked to BitDesignRevision)
- Cutters
- Consumables (brazing powders, flux, etc.)
- Tools and PPE
- Spare parts
- Services

Items represent the DESIGN/DEFINITION of things, not physical stock.
Physical stock is tracked in SerialUnit (serialized) or InventoryStock (non-serialized).
"""

from django.db import models
from django.core.exceptions import ValidationError
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin
from .reference import ItemCategory, UnitOfMeasure
# BitDesignRevision moved to engineering app - use string reference


class Item(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Master record for any inventory item.

    This is the "What is it?" layer - defining items independent of
    physical stock, location, condition, or ownership.

    For bit-related items, links to a specific BitDesignRevision (MAT).
    For non-bit items (consumables, tools), bit_design_revision is null.
    """
    # Primary identification
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Internal Stock Keeping Unit / Item Code"
    )
    name = models.CharField(
        max_length=200,
        help_text="Full descriptive name"
    )
    short_name = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Abbreviated name for displays"
    )

    # Classification
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name='items',
        help_text="Item category (determines if serialized, bit-related, etc.)"
    )
    uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='items',
        verbose_name="Unit of Measure",
        help_text="Default unit of measure for this item"
    )

    # Optional link to bit design (only for bit-related items)
    bit_design_revision = models.ForeignKey(
        'engineering.BitDesignRevision',  # ⚠️ String reference - model moved to engineering app
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='items',
        help_text="For bit-related items: the specific MAT/design revision"
    )

    # Inventory planning
    min_stock_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Minimum quantity to maintain in stock"
    )
    reorder_point = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Quantity at which to reorder"
    )
    reorder_qty = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Standard quantity to reorder"
    )
    safety_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Safety buffer quantity"
    )
    lead_time_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Standard lead time for procurement/production"
    )

    # Cost information
    standard_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Standard cost per unit"
    )
    last_purchase_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Cost from most recent purchase"
    )
    currency = models.CharField(
        max_length=3,
        default='SAR',
        help_text="Currency code (ISO 4217)"
    )

    # Status flags
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="False to discontinue item"
    )
    is_purchasable = models.BooleanField(
        default=True,
        help_text="Can be purchased from suppliers"
    )
    is_producible = models.BooleanField(
        default=False,
        help_text="Can be manufactured/assembled in-house"
    )
    is_sellable = models.BooleanField(
        default=False,
        help_text="Can be sold to customers"
    )
    is_stockable = models.BooleanField(
        default=True,
        help_text="Is physically stocked (False for services)"
    )

    # Supplier information (primary)
    primary_supplier = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Primary supplier name (FK to Supplier table in future)"
    )
    manufacturer_part_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Manufacturer's part number"
    )
    manufacturer_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Manufacturer name"
    )

    # Physical properties (for shipping, storage)
    weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Unit weight in kilograms"
    )
    volume_cbm = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Unit volume in cubic meters"
    )

    # Documentation
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed item description"
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes"
    )

    # Barcode / alternative codes
    barcode = models.CharField(
        max_length=100,
        blank=True,
        default="",
        db_index=True,
        help_text="Barcode value (EAN, UPC, etc.)"
    )
    alternative_codes = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional codes: {'old_sku': 'XXX', 'supplier_code': 'YYY'}"
    )

    class Meta:
        db_table = "inventory_item"
        verbose_name = "Item"
        verbose_name_plural = "Items"
        ordering = ['sku']
        indexes = [
            models.Index(fields=['sku'], name='ix_item_sku'),
            models.Index(fields=['category', 'is_active'], name='ix_item_cat_active'),
            models.Index(fields=['bit_design_revision'], name='ix_item_bdr'),
            models.Index(fields=['barcode'], name='ix_item_barcode'),
        ]

    def __str__(self):
        return f"{self.sku} - {self.short_name or self.name}"

    def clean(self):
        """Validate item data consistency."""
        super().clean()

        # If category is bit-related, bit_design_revision should be set
        if self.category and self.category.is_bit_related:
            if not self.bit_design_revision:
                raise ValidationError({
                    'bit_design_revision': (
                        "Bit-related items must have a design revision (MAT) linked."
                    )
                })

        # If category is serialized but is_stockable is False, that's inconsistent
        if self.category and self.category.is_serialized and not self.is_stockable:
            raise ValidationError({
                'is_stockable': "Serialized items must be stockable."
            })

        # Reorder point should be >= min_stock_qty
        if self.reorder_point < self.min_stock_qty:
            raise ValidationError({
                'reorder_point': "Reorder point should be >= minimum stock quantity."
            })

    @property
    def is_serialized(self):
        """Check if this item is tracked by serial number."""
        return self.category.is_serialized if self.category else False

    @property
    def mat_number(self):
        """Get the MAT number if this is a bit-related item."""
        if self.bit_design_revision:
            return self.bit_design_revision.mat_number
        return None

    @property
    def display_name(self):
        """Returns a user-friendly display name."""
        if self.bit_design_revision:
            return f"{self.sku} ({self.bit_design_revision.mat_number})"
        return self.sku

    def get_total_stock_quantity(self):
        """
        Get total quantity across all locations, conditions, and ownerships.

        For serialized items, returns count of SerialUnits.
        For non-serialized items, sums InventoryStock.quantity_on_hand.
        """
        if self.is_serialized:
            return self.serial_units.filter(
                status__in=['IN_STOCK', 'RESERVED']
            ).count()
        else:
            from django.db.models import Sum
            result = self.inventory_stocks.aggregate(
                total=Sum('quantity_on_hand')
            )
            return result['total'] or 0

    def get_available_quantity(self):
        """
        Get available quantity (on hand minus reserved).

        For serialized items, counts only IN_STOCK units.
        For non-serialized items, sums quantity_available.
        """
        if self.is_serialized:
            return self.serial_units.filter(status='IN_STOCK').count()
        else:
            from django.db.models import Sum, F
            result = self.inventory_stocks.aggregate(
                available=Sum(F('quantity_on_hand') - F('quantity_reserved'))
            )
            return result['available'] or 0
