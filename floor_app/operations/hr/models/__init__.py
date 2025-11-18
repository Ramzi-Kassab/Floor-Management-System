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

# HRMS Professional Features
from .leave import (
    LeavePolicy,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    LeaveRequestStatus,
)
from .attendance import (
    AttendanceRecord,
    OvertimeRequest,
    AttendanceSummary,
    AttendanceStatus,
    OvertimeType,
    OvertimeStatus,
)
from .training import (
    TrainingProgram,
    TrainingSession,
    EmployeeTraining,
    SkillMatrix,
    TrainingType,
    TrainingStatus,
)
from .document import (
    EmployeeDocument,
    DocumentRenewal,
    ExpiryAlert,
    DocumentType,
    DocumentStatus,
)
from .configuration import (
    OvertimeConfiguration,
    AttendanceConfiguration,
    DelayIncident,
    DelayReason,
)

# Import generic Address model (unified address table for entire system)
from floor_app.operations.models import Address


