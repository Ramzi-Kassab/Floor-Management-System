"""
Quality Management Models
"""
from .reference import (
    DefectCategory,
    RootCauseCategory,
    AcceptanceCriteriaTemplate,
)
from .ncr import (
    NonconformanceReport,
    NCRRootCauseAnalysis,
    NCRCorrectiveAction,
)
from .calibration import (
    CalibratedEquipment,
    CalibrationRecord,
)
from .disposition import (
    QualityDisposition,
)

__all__ = [
    # Reference tables
    'DefectCategory',
    'RootCauseCategory',
    'AcceptanceCriteriaTemplate',
    # NCR management
    'NonconformanceReport',
    'NCRRootCauseAnalysis',
    'NCRCorrectiveAction',
    # Calibration control
    'CalibratedEquipment',
    'CalibrationRecord',
    # Quality disposition
    'QualityDisposition',
]
