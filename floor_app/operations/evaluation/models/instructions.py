"""
Technical Instructions Engine - Template Models

These models define templates for automated technical instructions and
requirements that are triggered based on evaluation results and conditions.
"""

from django.db import models


class TechnicalInstructionTemplate(models.Model):
    """
    Template for technical instructions that can be automatically
    generated based on evaluation conditions.

    The template contains:
    - Condition rules (JSON) that trigger the instruction
    - Output template with placeholders
    - Severity and stage classification

    Examples:
    - "If more than 3 cutters marked X in gauge section, flag for gauge repair"
    - "If any pocket damage (P code), require pocket repair procedure"
    - "If thread inspection shows MAJOR_DAMAGE, escalate to engineering"
    """

    SCOPE_CHOICES = (
        ('EVALUATION_SESSION', 'Evaluation Session Level'),
        ('CELL_LEVEL', 'Individual Cell Level'),
        ('THREAD_LEVEL', 'Thread Inspection Level'),
        ('NDT_LEVEL', 'NDT Inspection Level'),
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

    # Template identification
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique template code (e.g., GAUGE_REPAIR_CHECK)"
    )

    name = models.CharField(
        max_length=200,
        help_text="Human-readable template name"
    )

    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of what this instruction template does"
    )

    # Scope and classification
    scope = models.CharField(
        max_length=30,
        choices=SCOPE_CHOICES,
        default='EVALUATION_SESSION',
        help_text="Level at which this instruction applies"
    )

    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default='EVALUATION',
        db_index=True,
        help_text="Production stage when this instruction is relevant"
    )

    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='INFO',
        db_index=True,
        help_text="Severity level of the instruction"
    )

    # Condition engine
    condition_json = models.JSONField(
        default=dict,
        help_text="JSON structure defining conditions that trigger this instruction"
    )

    # Output template
    output_template = models.TextField(
        help_text="Text template with placeholders (e.g., '{count} cutters need replacement in {section}')"
    )

    # Configuration
    auto_generate = models.BooleanField(
        default=True,
        help_text="Automatically generate when conditions are met"
    )

    requires_acknowledgment = models.BooleanField(
        default=False,
        help_text="Requires user acknowledgment before proceeding"
    )

    can_be_overridden = models.BooleanField(
        default=True,
        help_text="Can be overridden by authorized personnel"
    )

    override_requires_approval = models.BooleanField(
        default=False,
        help_text="Override requires higher-level approval"
    )

    # Priority
    priority = models.IntegerField(
        default=100,
        help_text="Higher priority instructions are processed first"
    )

    # Versioning
    version = models.PositiveIntegerField(
        default=1,
        help_text="Template version number"
    )

    effective_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this template version becomes effective"
    )

    effective_to = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this template version expires"
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evaluation_technical_instruction_template"
        verbose_name = "Technical Instruction Template"
        verbose_name_plural = "Technical Instruction Templates"
        ordering = ['-priority', 'stage', 'code']
        indexes = [
            models.Index(fields=['scope', 'stage', 'is_active'], name='ix_ti_template_scope_stage'),
            models.Index(fields=['severity', 'is_active'], name='ix_ti_template_severity'),
            models.Index(fields=['code'], name='ix_ti_template_code'),
            models.Index(fields=['-priority'], name='ix_ti_template_priority'),
        ]

    def __str__(self):
        return f"[{self.code}] {self.name} ({self.get_severity_display()})"

    @property
    def is_critical(self):
        """Check if this is a critical instruction."""
        return self.severity == 'CRITICAL'

    @property
    def is_effective(self):
        """Check if template is currently effective."""
        from django.utils import timezone
        now = timezone.now()

        if not self.is_active:
            return False

        if self.effective_from and now < self.effective_from:
            return False

        if self.effective_to and now > self.effective_to:
            return False

        return True


class RequirementTemplate(models.Model):
    """
    Template for mandatory requirements at various production stages.

    Requirements can include:
    - Documents (drawings, procedures, certifications)
    - Approvals (engineering sign-off, QC approval)
    - Materials (required parts, consumables)
    - Data (measurements, test results)
    """

    STAGE_CHOICES = (
        ('PRE_PRODUCTION', 'Pre-Production'),
        ('EVALUATION', 'During Evaluation'),
        ('PROCESSING', 'During Processing'),
        ('FINAL_QC', 'Final QC'),
        ('SHIPPING', 'Before Shipping'),
    )

    REQUIREMENT_TYPE_CHOICES = (
        ('DOCUMENT', 'Document Required'),
        ('APPROVAL', 'Approval Required'),
        ('MATERIAL', 'Material Required'),
        ('DATA', 'Data/Measurement Required'),
        ('INSPECTION', 'Inspection Required'),
        ('CERTIFICATION', 'Certification Required'),
    )

    # Template identification
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique requirement code (e.g., NDT_CERT_CHECK)"
    )

    name = models.CharField(
        max_length=200,
        help_text="Human-readable requirement name"
    )

    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of the requirement"
    )

    # Classification
    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default='EVALUATION',
        db_index=True,
        help_text="Production stage when this requirement applies"
    )

    requirement_type = models.CharField(
        max_length=20,
        choices=REQUIREMENT_TYPE_CHOICES,
        help_text="Type of requirement"
    )

    # Enforcement
    is_mandatory = models.BooleanField(
        default=True,
        help_text="If True, cannot proceed without satisfying this requirement"
    )

    can_be_waived = models.BooleanField(
        default=False,
        help_text="Can be waived by authorized personnel"
    )

    waiver_authority = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Role/position that can authorize waiver"
    )

    # Condition (optional: when does this requirement apply)
    condition_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Conditions under which this requirement applies"
    )

    # Instructions
    satisfaction_instructions = models.TextField(
        blank=True,
        default="",
        help_text="How to satisfy this requirement"
    )

    # Related documents
    reference_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="List of reference document codes/links"
    )

    # Timing
    lead_time_hours = models.IntegerField(
        default=0,
        help_text="Expected hours needed to satisfy this requirement"
    )

    # Display
    sort_order = models.IntegerField(default=0)
    icon = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Icon name for UI display"
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evaluation_requirement_template"
        verbose_name = "Requirement Template"
        verbose_name_plural = "Requirement Templates"
        ordering = ['stage', 'sort_order', 'code']
        indexes = [
            models.Index(fields=['stage', 'is_mandatory', 'is_active'], name='ix_req_template_stage'),
            models.Index(fields=['requirement_type', 'is_active'], name='ix_req_template_type'),
            models.Index(fields=['code'], name='ix_req_template_code'),
        ]

    def __str__(self):
        mandatory_str = "*" if self.is_mandatory else ""
        return f"[{self.code}] {self.name}{mandatory_str}"

    @property
    def is_blocking(self):
        """Check if this requirement blocks workflow progression."""
        return self.is_mandatory and not self.can_be_waived
