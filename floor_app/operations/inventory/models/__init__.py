# Inventory Models - PDC Bit Manufacturing & Repair
# Import all models here for easy access

from .bit_design import (
    BitDesignLevel,
    BitDesignType,
    BitDesign,
    BitDesignRevision,
)

from .bom import (
    BOMHeader,
    BOMLine,
)

from .reference import (
    ConditionType,
    OwnershipType,
    UnitOfMeasure,
    ItemCategory,
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
    # Bit Design & BOM
    'BitDesignLevel',
    'BitDesignType',
    'BitDesign',
    'BitDesignRevision',
    'BOMHeader',
    'BOMLine',
    # Reference tables
    'ConditionType',
    'OwnershipType',
    'UnitOfMeasure',
    'ItemCategory',
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

# ⚠️ MOVED TO ENGINEERING APP
# The following models have been moved to floor_app.operations.engineering:
# - BitDesignLevel, BitDesignType, BitDesign, BitDesignRevision (bit_design.py)
# - BOMHeader, BOMLine (bom.py)
# - RollerConeBitType, RollerConeBearing, RollerConeSeal (roller_cone.py)
# - RollerConeDesign, RollerConeComponent, RollerConeBOM (roller_cone.py)
