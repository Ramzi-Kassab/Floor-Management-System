# Inventory Models - PDC Bit Manufacturing & Repair
# Import all models here for easy access

from .reference import (
    ConditionType,
    OwnershipType,
    UnitOfMeasure,
    ItemCategory,
)

from .bit_design import (
    BitDesignLevel,
    BitDesignType,
    BitDesign,
    BitDesignRevision,
)

from .item import Item

from .stock import (
    Location,
    SerialUnit,
    SerialUnitMATHistory,
    InventoryStock,
)

from .attributes import (
    AttributeDefinition,
    CategoryAttributeMap,
    ItemAttributeValue,
)

from .bom import (
    BOMHeader,
    BOMLine,
)

from .transactions import (
    InventoryTransaction,
)

from .cutter import (
    CutterOwnershipCategory,
    CutterDetail,
    CutterPriceHistory,
    CutterInventorySummary,
)

from .cutter_bom_grid import (
    CutterBOMGridHeader,
    CutterBOMGridCell,
    CutterBOMSummary,
    CutterMapHeader,
    CutterMapCell,
    BOMUsageTracking,
)

__all__ = [
    # Reference tables
    'ConditionType',
    'OwnershipType',
    'UnitOfMeasure',
    'ItemCategory',
    # Bit design
    'BitDesignLevel',
    'BitDesignType',
    'BitDesign',
    'BitDesignRevision',
    # Item master
    'Item',
    # Physical stock
    'Location',
    'SerialUnit',
    'SerialUnitMATHistory',
    'InventoryStock',
    # Flexible attributes
    'AttributeDefinition',
    'CategoryAttributeMap',
    'ItemAttributeValue',
    # BOM
    'BOMHeader',
    'BOMLine',
    # Transactions
    'InventoryTransaction',
    # Cutter-specific
    'CutterOwnershipCategory',
    'CutterDetail',
    'CutterPriceHistory',
    'CutterInventorySummary',
    # Cutter BOM & Map Grid
    'CutterBOMGridHeader',
    'CutterBOMGridCell',
    'CutterBOMSummary',
    'CutterMapHeader',
    'CutterMapCell',
    'BOMUsageTracking',
]
