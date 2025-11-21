"""
⚠️  DEPRECATED - BitDesign Models have moved to engineering app

This file has been deprecated. BitDesign models are now in:
  floor_app.operations.engineering.models.bit_design

All imports should use:
  from floor_app.operations.engineering.models import (
      BitDesignLevel, BitDesignType, BitDesign, BitDesignRevision
  )

Models moved:
- BitDesignLevel
- BitDesignType
- BitDesign
- BitDesignRevision

Reason: Engineering owns design definitions (what needs to be built).
        Inventory owns physical stock (what we have).

Database: All db_table names preserved - no data migration needed.

Last Update: 2025-11-21
Related: Model Ownership Refactoring Task
"""

# Models moved to floor_app.operations.engineering.models.bit_design
# This file will be removed in a future update
