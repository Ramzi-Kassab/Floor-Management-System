"""
⚠️  DEPRECATED - BOM Admin has moved to engineering app

This file has been deprecated. BOM admin is now in:
  floor_app.operations.engineering.admin.bom

BOM models now belong to the engineering app as they define
design and manufacturing specifications, not inventory stock.

This file will be removed in a future update.

All BOM admin functionality (BOMHeader, BOMLine) is now registered
in the engineering app to prevent duplicate registration errors.

Last Update: 2025-11-20
Related: Model Ownership Refactoring Task
"""

# All admin registrations moved to floor_app.operations.engineering.admin.bom
# Import updated to use new location
from floor_app.operations.engineering.models import BOMHeader, BOMLine

# No admin registrations here - see engineering.admin.bom
