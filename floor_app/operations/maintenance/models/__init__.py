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
    MaintenanceRequest,
    MaintenanceWorkOrder,
    WorkOrderNote,
    WorkOrderPart,
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
    'MaintenanceWorkOrder',
    'WorkOrderNote',
    'WorkOrderPart',
    # Downtime & Impact
    'DowntimeEvent',
    'ProductionImpact',
    'LostSalesRecord',
]
