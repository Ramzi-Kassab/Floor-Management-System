# Evaluation & Technical Instructions Models - PDC Bit Manufacturing
# Import all models here for easy access

from .reference import (
    CutterEvaluationCode,
    FeatureCode,
    BitSection,
    BitType,
)

from .session import EvaluationSession

from .cell import EvaluationCell

from .inspection import (
    ThreadInspection,
    NDTInspection,
)

from .instructions import (
    TechnicalInstructionTemplate,
    RequirementTemplate,
)

from .instances import (
    TechnicalInstructionInstance,
    RequirementInstance,
)

from .audit import EvaluationChangeLog


# Backward compatibility wrapper for EvaluationSessionHistory
class EvaluationSessionHistoryManager:
    """Manager for backward compatibility with old EvaluationSessionHistory API."""

    def create(self, session, action, description, performed_by, **kwargs):
        """Create a change log entry using old API format."""
        # Map old action to new change_type
        action_map = {
            'CREATED': 'CREATE',
            'UPDATED': 'UPDATE',
            'DELETED': 'DELETE',
            'STATUS_CHANGE': 'STATUS_CHANGE',
            'APPROVED': 'APPROVAL',
        }
        change_type = action_map.get(action, 'UPDATE')

        return EvaluationChangeLog.objects.create(
            evaluation_session=session,
            change_type=change_type,
            change_stage='SYSTEM',
            model_name='EvaluationSession',
            object_id=session.pk if hasattr(session, 'pk') else None,
            reason=description,
            changed_by=performed_by,
            **kwargs
        )


class EvaluationSessionHistory:
    """Backward compatibility class for EvaluationSessionHistory."""
    objects = EvaluationSessionHistoryManager()


__all__ = [
    # Reference tables
    'CutterEvaluationCode',
    'FeatureCode',
    'BitSection',
    'BitType',
    # Core evaluation
    'EvaluationSession',
    'EvaluationCell',
    # Inspections
    'ThreadInspection',
    'NDTInspection',
    # Instruction templates
    'TechnicalInstructionTemplate',
    'RequirementTemplate',
    # Runtime instances
    'TechnicalInstructionInstance',
    'RequirementInstance',
    # Audit
    'EvaluationChangeLog',
    # Backward compatibility
    'EvaluationSessionHistory',
]
