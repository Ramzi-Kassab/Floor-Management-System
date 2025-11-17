"""
Runtime Instance Models for Technical Instructions and Requirements

These models track actual instances of instructions and requirements
that have been generated for specific evaluation sessions.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class TechnicalInstructionInstance(models.Model):
    """
    A specific instance of a technical instruction generated for an evaluation.

    Created when template conditions are met during evaluation.
    Tracks the resolved instruction text and user response.
    """

    STATUS_CHOICES = (
        ('SUGGESTED', 'Suggested'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('OVERRIDDEN', 'Overridden'),
        ('ACKNOWLEDGED', 'Acknowledged'),
    )

    STAGE_CHOICES = (
        ('PRE_PRODUCTION', 'Pre-Production'),
        ('EVALUATION', 'During Evaluation'),
        ('PROCESSING', 'During Processing'),
        ('FINAL_QC', 'Final QC'),
    )

    SEVERITY_CHOICES = (
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    )

    # Parent relationships
    evaluation_session = models.ForeignKey(
        'EvaluationSession',
        on_delete=models.CASCADE,
        related_name='instruction_instances',
        help_text="Evaluation session this instruction applies to"
    )

    template = models.ForeignKey(
        'TechnicalInstructionTemplate',
        on_delete=models.PROTECT,
        related_name='instances',
        help_text="Template this instruction was generated from"
    )

    # Resolved content
    resolved_text = models.TextField(
        help_text="Final instruction text with placeholders filled in"
    )

    # Classification (copied from template but can be modified)
    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        db_index=True,
        help_text="Production stage for this instruction"
    )

    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        db_index=True,
        help_text="Severity level of this instruction"
    )

    # User response
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SUGGESTED',
        db_index=True,
        help_text="Current status of the instruction"
    )

    # Related cells (optional: which cells triggered this instruction)
    related_cells = models.ManyToManyField(
        'EvaluationCell',
        blank=True,
        related_name='instruction_instances',
        help_text="Specific cells that triggered this instruction"
    )

    # Override handling
    override_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for overriding/rejecting the instruction"
    )

    override_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instruction_overrides',
        help_text="User who overrode the instruction"
    )

    override_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instruction_override_approvals',
        help_text="User who approved the override (if required)"
    )

    # Acknowledgment tracking
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instruction_acknowledgments',
        help_text="User who acknowledged the instruction"
    )

    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the instruction was acknowledged"
    )

    # Context data (for reference)
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Snapshot of data used to generate this instruction"
    )

    # Timing
    generated_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this instruction was generated"
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the instruction was resolved (accepted/rejected/overridden)"
    )

    # Priority (inherited from template but can be adjusted)
    priority = models.IntegerField(
        default=100,
        help_text="Priority for display ordering"
    )

    class Meta:
        db_table = "evaluation_technical_instruction_instance"
        verbose_name = "Technical Instruction Instance"
        verbose_name_plural = "Technical Instruction Instances"
        ordering = ['-priority', '-severity', '-generated_at']
        indexes = [
            models.Index(
                fields=['evaluation_session', 'status'],
                name='ix_ti_inst_session_status'
            ),
            models.Index(
                fields=['evaluation_session', 'stage'],
                name='ix_ti_inst_session_stage'
            ),
            models.Index(
                fields=['status', 'severity'],
                name='ix_ti_inst_status_severity'
            ),
            models.Index(
                fields=['template', '-generated_at'],
                name='ix_ti_inst_template'
            ),
        ]

    def __str__(self):
        return f"Inst-{self.pk}: {self.template.code} ({self.status})"

    @property
    def is_pending(self):
        """Check if instruction needs user action."""
        return self.status == 'SUGGESTED'

    @property
    def is_resolved(self):
        """Check if instruction has been resolved."""
        return self.status in ('ACCEPTED', 'REJECTED', 'OVERRIDDEN', 'ACKNOWLEDGED')

    @property
    def is_critical(self):
        """Check if this is a critical instruction."""
        return self.severity == 'CRITICAL'

    def accept(self, user=None):
        """Accept the instruction."""
        self.status = 'ACCEPTED'
        self.resolved_at = timezone.now()
        if user:
            self.acknowledged_by = user
            self.acknowledged_at = timezone.now()
        self.save(update_fields=['status', 'resolved_at', 'acknowledged_by', 'acknowledged_at'])

    def reject(self, reason='', user=None):
        """Reject the instruction."""
        self.status = 'REJECTED'
        self.override_reason = reason
        self.resolved_at = timezone.now()
        if user:
            self.override_by = user
        self.save(update_fields=['status', 'override_reason', 'resolved_at', 'override_by'])

    def override(self, reason, user=None, approver=None):
        """Override the instruction with reason."""
        self.status = 'OVERRIDDEN'
        self.override_reason = reason
        self.resolved_at = timezone.now()
        if user:
            self.override_by = user
        if approver:
            self.override_approved_by = approver
        self.save(update_fields=[
            'status', 'override_reason', 'resolved_at',
            'override_by', 'override_approved_by'
        ])

    def acknowledge(self, user=None):
        """Acknowledge the instruction (for INFO level)."""
        self.status = 'ACKNOWLEDGED'
        self.acknowledged_at = timezone.now()
        self.resolved_at = timezone.now()
        if user:
            self.acknowledged_by = user
        self.save(update_fields=['status', 'acknowledged_at', 'resolved_at', 'acknowledged_by'])


class RequirementInstance(models.Model):
    """
    A specific instance of a requirement for an evaluation session.

    Tracks whether the requirement has been satisfied and by whom.
    """

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SATISFIED', 'Satisfied'),
        ('NOT_APPLICABLE', 'Not Applicable'),
        ('WAIVED', 'Waived'),
    )

    # Parent relationships
    evaluation_session = models.ForeignKey(
        'EvaluationSession',
        on_delete=models.CASCADE,
        related_name='requirement_instances',
        help_text="Evaluation session this requirement applies to"
    )

    template = models.ForeignKey(
        'RequirementTemplate',
        on_delete=models.PROTECT,
        related_name='instances',
        help_text="Requirement template"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True,
        help_text="Current status of the requirement"
    )

    # Satisfaction tracking
    satisfied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirements_satisfied',
        help_text="User who satisfied/verified the requirement"
    )

    satisfied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the requirement was satisfied"
    )

    # Documentation
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes about satisfaction or waiver"
    )

    evidence_refs = models.JSONField(
        default=list,
        blank=True,
        help_text="References to evidence documents/files"
    )

    # Waiver handling (if applicable)
    waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirements_waived',
        help_text="User who waived the requirement"
    )

    waiver_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for waiving the requirement"
    )

    waiver_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirement_waiver_approvals',
        help_text="Authority who approved the waiver"
    )

    # Due date tracking
    due_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this requirement is due"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this instance was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this instance was last updated"
    )

    class Meta:
        db_table = "evaluation_requirement_instance"
        verbose_name = "Requirement Instance"
        verbose_name_plural = "Requirement Instances"
        ordering = ['-template__is_mandatory', 'template__sort_order']
        indexes = [
            models.Index(
                fields=['evaluation_session', 'status'],
                name='ix_req_inst_session_status'
            ),
            models.Index(
                fields=['status', '-created_at'],
                name='ix_req_inst_status_created'
            ),
            models.Index(
                fields=['template', 'status'],
                name='ix_req_inst_template_status'
            ),
            models.Index(
                fields=['due_at'],
                name='ix_req_inst_due_at'
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['evaluation_session', 'template'],
                name='uq_req_inst_session_template'
            ),
        ]

    def __str__(self):
        return f"Req-{self.template.code}: {self.status}"

    @property
    def is_blocking(self):
        """Check if this requirement blocks workflow."""
        return (
            self.template.is_mandatory and
            self.status not in ('SATISFIED', 'NOT_APPLICABLE', 'WAIVED')
        )

    @property
    def is_overdue(self):
        """Check if requirement is overdue."""
        if self.due_at and self.status == 'PENDING':
            return timezone.now() > self.due_at
        return False

    @property
    def is_satisfied(self):
        """Check if requirement is satisfied."""
        return self.status in ('SATISFIED', 'NOT_APPLICABLE', 'WAIVED')

    def satisfy(self, user=None, notes='', evidence=None):
        """Mark requirement as satisfied."""
        self.status = 'SATISFIED'
        self.satisfied_at = timezone.now()
        if user:
            self.satisfied_by = user
        if notes:
            self.notes = notes
        if evidence:
            self.evidence_refs = evidence
        self.save(update_fields=[
            'status', 'satisfied_at', 'satisfied_by', 'notes', 'evidence_refs', 'updated_at'
        ])

    def mark_not_applicable(self, reason='', user=None):
        """Mark requirement as not applicable."""
        self.status = 'NOT_APPLICABLE'
        self.notes = reason
        if user:
            self.satisfied_by = user
            self.satisfied_at = timezone.now()
        self.save(update_fields=['status', 'notes', 'satisfied_by', 'satisfied_at', 'updated_at'])

    def waive(self, reason, waived_by=None, approved_by=None):
        """Waive the requirement with proper authorization."""
        self.status = 'WAIVED'
        self.waiver_reason = reason
        if waived_by:
            self.waived_by = waived_by
        if approved_by:
            self.waiver_approved_by = approved_by
        self.satisfied_at = timezone.now()
        self.save(update_fields=[
            'status', 'waiver_reason', 'waived_by',
            'waiver_approved_by', 'satisfied_at', 'updated_at'
        ])

    def reset(self):
        """Reset requirement back to pending."""
        self.status = 'PENDING'
        self.satisfied_by = None
        self.satisfied_at = None
        self.notes = ''
        self.evidence_refs = []
        self.waived_by = None
        self.waiver_reason = ''
        self.waiver_approved_by = None
        self.save()
