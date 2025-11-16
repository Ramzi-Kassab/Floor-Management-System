# floor_app/operations/hr/models/__init__.py
# Import HR-specific models
from .phone import *
from .email import *
from .people import *
from .employee import *
from .qualification import *
from .department import *
from .position import *
from .audit_log import *

# Import generic Address model (unified address table for entire system)
from floor_app.operations.models import Address


