"""
⚠️  DEPRECATED - BitDesign Admin has moved to engineering app

This file has been deprecated. BitDesign admin is now in:
  floor_app.operations.engineering.admin.bit_design

BitDesign models now belong to the engineering app as they define
design specifications, not inventory stock.

This file will be removed in a future update.

All BitDesign admin functionality (BitDesignLevel, BitDesignType,
BitDesign, BitDesignRevision) is now registered in the engineering app
to prevent duplicate registration errors.

Last Update: 2025-11-21
Related: Model Ownership Refactoring Task
"""

# All admin registrations moved to floor_app.operations.engineering.admin.bit_design
# Import updated to use new location
from floor_app.operations.engineering.models import (
    BitDesignLevel,
    BitDesignType,
    BitDesign,
    BitDesignRevision,
)

# No admin registrations here - see engineering.admin.bit_design
