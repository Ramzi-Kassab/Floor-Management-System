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
]
