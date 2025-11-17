"""
Maintenance & Asset Management Models

Complete CMMS (Computerized Maintenance Management System) for factory equipment.
"""

# Asset and Equipment Registry
from .asset import (
    AssetCategory,
    AssetLocation,
    Asset,
    AssetDocument,
)

# Preventive Maintenance
from .preventive import (
    PMPlan,
    PMSchedule,
    PMTask,
)

# Corrective Maintenance
from .corrective import (
    MaintenanceRequest,
    WorkOrder,
    WorkOrderAttachment,
)

# Downtime and Impact Tracking
from .downtime import (
    DowntimeEvent,
    ProductionImpact,
    LostSales,
)

# Parts and Consumables
from .parts import (
    PartsUsage,
)

__all__ = [
    # Assets
    'AssetCategory',
    'AssetLocation',
    'Asset',
    'AssetDocument',
    # Preventive Maintenance
    'PMPlan',
    'PMSchedule',
    'PMTask',
    # Corrective Maintenance
    'MaintenanceRequest',
    'WorkOrder',
    'WorkOrderAttachment',
    # Downtime
    'DowntimeEvent',
    'ProductionImpact',
    'LostSales',
    # Parts
    'PartsUsage',
]
