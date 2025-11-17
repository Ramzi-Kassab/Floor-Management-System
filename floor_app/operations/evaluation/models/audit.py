"""
Audit and Change Tracking Models

These models provide detailed change history for evaluation data,
tracking who changed what, when, and why.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class EvaluationChangeLog(models.Model):
    """
    Detailed change log for evaluation data.

    Tracks every modification to evaluation sessions and cells,
    providing a complete audit trail for quality assurance and
    regulatory compliance.
    """

    CHANGE_STAGE_CHOICES = (
        ('EVALUATOR', 'Evaluator Stage'),
        ('ENGINEER', 'Engineering Review'),
        ('ADMIN', 'Administrative Override'),
        ('SYSTEM', 'System Generated'),
    )

    CHANGE_TYPE_CHOICES = (
        ('CREATE', 'Record Created'),
        ('UPDATE', 'Field Updated'),
        ('DELETE', 'Record Deleted'),
        ('RESTORE', 'Record Restored'),
        ('STATUS_CHANGE', 'Status Changed'),
        ('APPROVAL', 'Approval Action'),
        ('OVERRIDE', 'Override Action'),
    )

    # Parent session (always tracked)
    evaluation_session = models.ForeignKey(
        'EvaluationSession',
        on_delete=models.CASCADE,
        related_name='change_logs',
        help_text="Evaluation session being tracked"
    )

    # Optional cell reference (for cell-specific changes)
    evaluation_cell = models.ForeignKey(
        'EvaluationCell',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='change_logs',
        help_text="Specific cell that was changed (if applicable)"
    )

    # Thread or NDT inspection reference (optional)
    thread_inspection = models.ForeignKey(
        'ThreadInspection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='change_logs',
        help_text="Thread inspection that was changed (if applicable)"
    )

    ndt_inspection = models.ForeignKey(
        'NDTInspection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='change_logs',
        help_text="NDT inspection that was changed (if applicable)"
    )

    # Who made the change
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='evaluation_changes',
        help_text="User who made the change"
    )

    # Change context
    change_stage = models.CharField(
        max_length=20,
        choices=CHANGE_STAGE_CHOICES,
        db_index=True,
        help_text="Stage/role when change was made"
    )

    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPE_CHOICES,
        default='UPDATE',
        db_index=True,
        help_text="Type of change"
    )

    # What was changed
    model_name = models.CharField(
        max_length=100,
        help_text="Name of the model that was changed"
    )

    object_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID of the specific object changed"
    )

    field_changed = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Specific field that was modified"
    )

    # Values
    old_value = models.TextField(
        blank=True,
        default="",
        help_text="Previous value (serialized)"
    )

    new_value = models.TextField(
        blank=True,
        default="",
        help_text="New value (serialized)"
    )

    # Reason and justification
    reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for the change"
    )

    # Additional context
    additional_context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context data for the change"
    )

    # IP and session info (for security audit)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )

    user_agent = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="User agent/browser information"
    )

    # Timing
    changed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the change was made"
    )

    class Meta:
        db_table = "evaluation_change_log"
        verbose_name = "Evaluation Change Log"
        verbose_name_plural = "Evaluation Change Logs"
        ordering = ['-changed_at']
        indexes = [
            models.Index(
                fields=['evaluation_session', '-changed_at'],
                name='ix_eval_changelog_session'
            ),
            models.Index(
                fields=['changed_by', '-changed_at'],
                name='ix_eval_changelog_user'
            ),
            models.Index(
                fields=['change_stage', '-changed_at'],
                name='ix_eval_changelog_stage'
            ),
            models.Index(
                fields=['change_type', '-changed_at'],
                name='ix_eval_changelog_type'
            ),
            models.Index(
                fields=['evaluation_cell', '-changed_at'],
                name='ix_eval_changelog_cell'
            ),
            models.Index(
                fields=['field_changed', '-changed_at'],
                name='ix_eval_changelog_field'
            ),
        ]

    def __str__(self):
        cell_str = f" Cell-{self.evaluation_cell_id}" if self.evaluation_cell_id else ""
        return f"[{self.changed_at.strftime('%Y-%m-%d %H:%M')}] {self.change_stage} - {self.field_changed or self.change_type}{cell_str}"

    @property
    def is_significant_change(self):
        """Check if this is a significant change (not just minor edit)."""
        significant_fields = [
            'cutter_code', 'status', 'result', 'severity',
            'approved_at', 'locked_at', 'is_last_known_state'
        ]
        return (
            self.change_type in ('STATUS_CHANGE', 'APPROVAL', 'OVERRIDE') or
            self.field_changed in significant_fields
        )

    @property
    def change_summary(self):
        """Generate a human-readable change summary."""
        if self.change_type == 'CREATE':
            return f"Created {self.model_name}"
        elif self.change_type == 'DELETE':
            return f"Deleted {self.model_name}"
        elif self.change_type == 'STATUS_CHANGE':
            return f"Status changed from '{self.old_value}' to '{self.new_value}'"
        elif self.field_changed:
            return f"Changed {self.field_changed}: '{self.old_value}' -> '{self.new_value}'"
        else:
            return f"{self.get_change_type_display()}"

    @classmethod
    def log_change(cls, session, user, stage, change_type, model_name,
                   object_id=None, field_changed='', old_value='', new_value='',
                   reason='', cell=None, thread_insp=None, ndt_insp=None,
                   context=None, ip_address=None, user_agent=''):
        """
        Convenience method to create a change log entry.

        Args:
            session: EvaluationSession instance
            user: User who made the change
            stage: Change stage (EVALUATOR, ENGINEER, ADMIN, SYSTEM)
            change_type: Type of change (CREATE, UPDATE, DELETE, etc.)
            model_name: Name of the model being changed
            object_id: ID of the object (optional)
            field_changed: Specific field changed (optional)
            old_value: Previous value (optional)
            new_value: New value (optional)
            reason: Reason for change (optional)
            cell: Related EvaluationCell (optional)
            thread_insp: Related ThreadInspection (optional)
            ndt_insp: Related NDTInspection (optional)
            context: Additional context dict (optional)
            ip_address: User's IP address (optional)
            user_agent: User's browser info (optional)
        """
        return cls.objects.create(
            evaluation_session=session,
            evaluation_cell=cell,
            thread_inspection=thread_insp,
            ndt_inspection=ndt_insp,
            changed_by=user,
            change_stage=stage,
            change_type=change_type,
            model_name=model_name,
            object_id=object_id,
            field_changed=field_changed,
            old_value=str(old_value) if old_value is not None else '',
            new_value=str(new_value) if new_value is not None else '',
            reason=reason,
            additional_context=context or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def log_session_change(cls, session, user, stage, field_changed, old_value, new_value, reason=''):
        """Log a change to the evaluation session itself."""
        return cls.log_change(
            session=session,
            user=user,
            stage=stage,
            change_type='UPDATE',
            model_name='EvaluationSession',
            object_id=session.pk,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
        )

    @classmethod
    def log_cell_change(cls, cell, user, stage, field_changed, old_value, new_value, reason=''):
        """Log a change to an evaluation cell."""
        return cls.log_change(
            session=cell.evaluation_session,
            user=user,
            stage=stage,
            change_type='UPDATE',
            model_name='EvaluationCell',
            object_id=cell.pk,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            cell=cell,
        )

    @classmethod
    def log_status_change(cls, session, user, stage, old_status, new_status, reason=''):
        """Log a session status change."""
        return cls.log_change(
            session=session,
            user=user,
            stage=stage,
            change_type='STATUS_CHANGE',
            model_name='EvaluationSession',
            object_id=session.pk,
            field_changed='status',
            old_value=old_status,
            new_value=new_status,
            reason=reason,
        )

    @classmethod
    def log_approval(cls, session, user, approval_type, reason=''):
        """Log an approval action."""
        return cls.log_change(
            session=session,
            user=user,
            stage='ENGINEER',
            change_type='APPROVAL',
            model_name='EvaluationSession',
            object_id=session.pk,
            field_changed=approval_type,
            new_value=timezone.now().isoformat(),
            reason=reason,
        )
