# Production & Evaluation Models - PDC Bit Manufacturing & Repair
# Import all models here for easy access

from .reference import (
    OperationDefinition,
    CutterSymbol,
    ChecklistTemplate,
    ChecklistItemTemplate,
)

from .batch import BatchOrder

from .job_card import JobCard

from .routing import (
    JobRoute,
    JobRouteStep,
)

from .evaluation import (
    CutterLayout,
    CutterLocation,
    JobCutterEvaluationHeader,
    JobCutterEvaluationDetail,
    JobCutterEvaluationOverride,
)

from .inspection import (
    ApiThreadInspection,
    NdtReport,
)

from .checklist import (
    JobChecklistInstance,
    JobChecklistItem,
)

__all__ = [
    # Reference tables
    'OperationDefinition',
    'CutterSymbol',
    'ChecklistTemplate',
    'ChecklistItemTemplate',
    # Batch layer
    'BatchOrder',
    # Job card layer
    'JobCard',
    # Routing layer
    'JobRoute',
    'JobRouteStep',
    # Evaluation layer
    'CutterLayout',
    'CutterLocation',
    'JobCutterEvaluationHeader',
    'JobCutterEvaluationDetail',
    'JobCutterEvaluationOverride',
    # Inspection layer
    'ApiThreadInspection',
    'NdtReport',
    # Checklist layer
    'JobChecklistInstance',
    'JobChecklistItem',
]
