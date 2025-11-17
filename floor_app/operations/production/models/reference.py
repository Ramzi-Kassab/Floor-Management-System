"""
Reference/Lookup Tables for Production Module

These are configuration tables that define:
- Operation definitions (process steps)
- Cutter symbols and their meanings
- Checklist templates
"""

from django.db import models
from floor_app.mixins import AuditMixin, SoftDeleteMixin


class OperationDefinition(AuditMixin, SoftDeleteMixin):
    """
    Master list of production operations/process steps.

    Examples: Pre-Evaluation, De-Braze, Grinding, Brazing, Final Inspection, etc.
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique operation code (e.g., EVAL-PRE, GRIND-01)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Operation name"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of the operation"
    )

    # Categorization
    department = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Department responsible (e.g., Production-PDC, QC, NDT)"
    )
    operation_group = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Operation group (e.g., Brazing, Grinding, Inspection)"
    )

    # Defaults for routing
    default_sequence = models.IntegerField(
        default=100,
        help_text="Default position in route sequence"
    )
    default_duration_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected duration in hours"
    )

    # Flags
    requires_operator = models.BooleanField(
        default=True,
        help_text="Operation requires operator assignment"
    )
    requires_supervisor_approval = models.BooleanField(
        default=False,
        help_text="Requires supervisor sign-off"
    )
    is_quality_checkpoint = models.BooleanField(
        default=False,
        help_text="This is a quality control checkpoint"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "production_operation_definition"
        verbose_name = "Operation Definition"
        verbose_name_plural = "Operation Definitions"
        ordering = ['sort_order', 'default_sequence', 'code']
        indexes = [
            models.Index(fields=['code'], name='ix_opdef_code'),
            models.Index(fields=['department', 'is_active'], name='ix_opdef_dept_active'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class CutterSymbol(AuditMixin):
    """
    Defines the symbols used in cutter evaluation maps.

    Examples:
    - X: Damaged, must be replaced
    - O: OK, good condition
    - S: Needs braze build-up (spin and add braze)
    - R: Rotate to expose new edge
    - L: Lost cutter (clean pocket)
    - V: Build-up fins
    - P: Pockets
    - I: Impact arrestors
    """

    ACTION_CHOICES = (
        ('REPLACE', 'Replace Cutter'),
        ('KEEP', 'Keep As-Is'),
        ('REPAIR_BRAZE', 'Repair with Braze Build-up'),
        ('ROTATE', 'Rotate Cutter'),
        ('CLEAN', 'Clean/Rebuild Pocket'),
        ('BUILD_UP', 'Build-up Structure'),
        ('INSPECT', 'Further Inspection Needed'),
        ('OTHER', 'Other Action'),
    )

    symbol = models.CharField(
        max_length=5,
        unique=True,
        db_index=True,
        help_text="Symbol character (X, O, S, R, L, etc.)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Symbol meaning"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed description of what this symbol means"
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Primary action to take for this symbol"
    )

    # Costing flags
    is_replacement = models.BooleanField(
        default=False,
        help_text="Symbol indicates cutter replacement (for quotation)"
    )
    is_repair = models.BooleanField(
        default=False,
        help_text="Symbol indicates repair work (for quotation)"
    )
    cost_multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        help_text="Cost multiplier for quotation calculations"
    )

    color_code = models.CharField(
        max_length=20,
        blank=True,
        default="#000000",
        help_text="Color code for UI display (hex)"
    )

    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "production_cutter_symbol"
        verbose_name = "Cutter Symbol"
        verbose_name_plural = "Cutter Symbols"
        ordering = ['sort_order', 'symbol']

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class ChecklistTemplate(AuditMixin, SoftDeleteMixin):
    """
    Template for reusable checklists.

    Examples: Production Release Checklist, Final QC Checklist, Packing Checklist
    """

    APPLIES_TO_CHOICES = (
        ('JOB_CARD', 'Job Card'),
        ('BATCH', 'Batch Order'),
        ('ROUTE_STEP', 'Route Step'),
        ('SERIAL_UNIT', 'Serial Unit'),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Checklist template code"
    )
    name = models.CharField(
        max_length=100,
        help_text="Checklist name"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Purpose and usage of this checklist"
    )

    applies_to = models.CharField(
        max_length=20,
        choices=APPLIES_TO_CHOICES,
        default='JOB_CARD',
        help_text="What entity this checklist applies to"
    )

    # Workflow integration
    required_for_release = models.BooleanField(
        default=False,
        help_text="All items must be completed before release"
    )
    auto_create_on_job = models.BooleanField(
        default=False,
        help_text="Automatically create instance when job card is created"
    )

    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "production_checklist_template"
        verbose_name = "Checklist Template"
        verbose_name_plural = "Checklist Templates"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ChecklistItemTemplate(AuditMixin):
    """
    Individual items within a checklist template.
    """

    template = models.ForeignKey(
        ChecklistTemplate,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Parent checklist template"
    )

    text = models.CharField(
        max_length=500,
        help_text="Checklist item text/question"
    )

    required_role = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Role required to complete this item (e.g., QC Inspector, Supervisor)"
    )

    is_mandatory = models.BooleanField(
        default=True,
        help_text="Item must be completed"
    )

    sequence = models.IntegerField(
        default=10,
        help_text="Order in checklist"
    )

    help_text = models.TextField(
        blank=True,
        default="",
        help_text="Additional guidance for completing this item"
    )

    class Meta:
        db_table = "production_checklist_item_template"
        verbose_name = "Checklist Item Template"
        verbose_name_plural = "Checklist Item Templates"
        ordering = ['template', 'sequence']
        indexes = [
            models.Index(fields=['template', 'sequence'], name='ix_clitem_tmpl_seq'),
        ]

    def __str__(self):
        return f"{self.template.code} #{self.sequence}: {self.text[:50]}"
