# floor_app/operations/maintenance/models/__init__.py
"""
Maintenance, Asset & Downtime Module - Models
"""
from .asset import (
    AssetCategory,
    AssetLocation,
    Asset,
    AssetDocument,
    AssetMeterReading,
)
from .preventive import (
    PMTemplate,
    PMSchedule,
    PMTask,
)
from .workorder import (
    WorkOrderNote,
    WorkOrderPart,
)
from .corrective import (
    MaintenanceRequest,
    WorkOrder,
    WorkOrderAttachment,
)
from .parts import (
    PartsUsage,
)
from .downtime import (
    DowntimeEvent,
    ProductionImpact,
    LostSalesRecord,
)

__all__ = [
    # Assets
    'AssetCategory',
    'AssetLocation',
    'Asset',
    'AssetDocument',
    'AssetMeterReading',
    # Preventive Maintenance
    'PMTemplate',
    'PMSchedule',
    'PMTask',
    # Work Orders
    'MaintenanceRequest',
    'WorkOrder',
    'WorkOrderNote',
    'WorkOrderPart',
    'WorkOrderAttachment',
    'PartsUsage',
    # Downtime & Impact
    'DowntimeEvent',
    'ProductionImpact',
    'LostSalesRecord',
]
