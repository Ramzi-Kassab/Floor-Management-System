"""
⚠️  DEPRECATED - BOM Models have moved to engineering app

This file has been deprecated. BOM models are now in:
  floor_app.operations.engineering.models.bom

All imports should use:
  from floor_app.operations.engineering.models import BOMHeader, BOMLine

Models moved:
- BOMHeader
- BOMLine

Reason: Engineering owns BOM definitions (what components are needed).
        Inventory owns physical stock (what we have).

Database: All db_table names preserved - no data migration needed.

Last Update: 2025-11-21
Related: Model Ownership Refactoring Task
"""

# Models moved to floor_app.operations.engineering.models.bom
# This file will be removed in a future update
