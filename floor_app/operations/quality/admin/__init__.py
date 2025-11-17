"""
Quality Management Admin Configuration
"""
from .reference import (
    DefectCategoryAdmin,
    RootCauseCategoryAdmin,
    AcceptanceCriteriaTemplateAdmin,
)
from .ncr import (
    NonconformanceReportAdmin,
    NCRRootCauseAnalysisAdmin,
    NCRCorrectiveActionAdmin,
)
from .calibration import (
    CalibratedEquipmentAdmin,
    CalibrationRecordAdmin,
)
from .disposition import (
    QualityDispositionAdmin,
)

__all__ = [
    'DefectCategoryAdmin',
    'RootCauseCategoryAdmin',
    'AcceptanceCriteriaTemplateAdmin',
    'NonconformanceReportAdmin',
    'NCRRootCauseAnalysisAdmin',
    'NCRCorrectiveActionAdmin',
    'CalibratedEquipmentAdmin',
    'CalibrationRecordAdmin',
    'QualityDispositionAdmin',
]
