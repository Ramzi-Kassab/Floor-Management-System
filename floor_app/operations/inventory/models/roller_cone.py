"""
⚠️  DEPRECATED - RollerCone Models have moved to engineering app

This file has been deprecated. RollerCone models are now in:
  floor_app.operations.engineering.models.roller_cone

All imports should use:
  from floor_app.operations.engineering.models import (
      RollerConeBitType, RollerConeBearing, RollerConeSeal,
      RollerConeDesign, RollerConeComponent, RollerConeBOM
  )

Models moved:
- RollerConeBitType
- RollerConeBearing
- RollerConeSeal
- RollerConeDesign
- RollerConeComponent
- RollerConeBOM

Reason: Engineering owns design definitions (roller cone specifications).
        Inventory owns physical stock (what we have).

Database: All db_table names preserved - no data migration needed.

Last Update: 2025-11-21
Related: Model Ownership Refactoring Task
"""

# Models moved to floor_app.operations.engineering.models.roller_cone
# This file will be removed in a future update
