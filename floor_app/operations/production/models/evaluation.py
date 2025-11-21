"""
Evaluation Layer - Cutter Maps and Condition Assessment

Captures per-cutter condition using symbols (X/O/S/R/L/V/P/I etc.)
Supports internal (ARDT) and external (LSTK, ARAMCO) evaluation views.
Supports engineer override of evaluations.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin


class CutterLayout(AuditMixin):
    """
    Defines the cutter layout for a bit design.

    Each bit design (MAT) has a specific cutter arrangement.
    This model defines the grid structure for evaluation.
    """

    design_revision = models.ForeignKey(
        'engineering.BitDesignRevision',
        on_delete=models.CASCADE,
        related_name='cutter_layouts',
        help_text="Bit design revision this layout belongs to"
    )

    name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Layout name (e.g., 'Standard 6-blade')"
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of layout"
    )

    # Grid structure
    total_rows = models.IntegerField(
        default=10,
        help_text="Total number of rows in grid"
    )
    total_columns = models.IntegerField(
        default=20,
        help_text="Total number of columns in grid"
    )

    # Alternative structure (PDC specific)
    num_blades = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of blades on bit"
    )
    cutters_per_blade = models.IntegerField(
        null=True,
        blank=True,
        help_text="Average cutters per blade"
    )

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "production_cutter_layout"
        verbose_name = "Cutter Layout"
        verbose_name_plural = "Cutter Layouts"
        indexes = [
            models.Index(fields=['design_revision'], name='ix_cutlayout_design'),
        ]

    def __str__(self):
        return f"Layout for {self.design_revision.mat_number}"


class CutterLocation(AuditMixin):
    """
    Individual cutter position in a layout.

    Each position has coordinates and metadata for evaluation mapping.
    """

    layout = models.ForeignKey(
        CutterLayout,
        on_delete=models.CASCADE,
        related_name='locations',
        help_text="Parent layout"
    )

    # Grid coordinates
    row = models.IntegerField(
        help_text="Row number (1-based)"
    )
    column = models.IntegerField(
        help_text="Column number (1-based)"
    )

    # Alternative coordinates (PDC specific)
    blade_number = models.IntegerField(
        null=True,
        blank=True,
        help_text="Blade number (1-based)"
    )
    position_on_blade = models.IntegerField(
        null=True,
        blank=True,
        help_text="Position on blade (1=center, increasing outward)"
    )

    # Display
    label = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Display label (e.g., '1A', '2B', 'B1-P3')"
    )

    # Cutter spec (expected cutter type)
    expected_cutter_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Expected cutter type at this location"
    )
    expected_cutter_size = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Expected cutter size (e.g., '13mm', '16mm')"
    )

    # Flags
    is_primary = models.BooleanField(
        default=True,
        help_text="Primary cutter (vs backup/spare)"
    )
    is_critical = models.BooleanField(
        default=False,
        help_text="Critical cutter location"
    )

    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "production_cutter_location"
        verbose_name = "Cutter Location"
        verbose_name_plural = "Cutter Locations"
        ordering = ['layout', 'sort_order', 'row', 'column']
        unique_together = [['layout', 'row', 'column']]
        indexes = [
            models.Index(fields=['layout', 'row', 'column'], name='ix_cutloc_layout_pos'),
        ]

    def __str__(self):
        if self.label:
            return f"{self.layout} - {self.label}"
        return f"{self.layout} - R{self.row}C{self.column}"


class JobCutterEvaluationHeader(AuditMixin):
    """
    Header for a cutter evaluation session.

    A job card can have multiple evaluations:
    - Internal ARDT evaluation
    - External LSTK evaluation
    - Customer-specific (ARAMCO) evaluation
    - Engineer override evaluation
    """

    EVALUATION_TYPE_CHOICES = (
        ('INTERNAL_ARDT', 'Internal ARDT Evaluation'),
        ('ENGINEER_OVERRIDE', 'Engineer Override'),
        ('EXTERNAL_LSTK', 'External LSTK Evaluation'),
        ('CUSTOMER_ARAMCO', 'ARAMCO Customer Evaluation'),
        ('CUSTOMER_OTHER', 'Other Customer Evaluation'),
        ('FINAL_QC', 'Final QC Evaluation'),
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    job_card = models.ForeignKey(
        'JobCard',
        on_delete=models.CASCADE,
        related_name='cutter_evaluations',
        help_text="Job card being evaluated"
    )

    evaluation_type = models.CharField(
        max_length=30,
        choices=EVALUATION_TYPE_CHOICES,
        default='INTERNAL_ARDT',
        db_index=True
    )

    revision_number = models.IntegerField(
        default=1,
        help_text="Evaluation revision number"
    )

    # Layout reference (which cutter map to use)
    layout = models.ForeignKey(
        CutterLayout,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluations',
        help_text="Cutter layout used for this evaluation"
    )

    # Evaluator info
    evaluated_by = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cutter_evaluations',
        help_text="Employee who performed evaluation"
    )
    evaluated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When evaluation was performed"
    )

    # Review/Approval
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_evaluations',
        help_text="User who reviewed this evaluation"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True
    )

    # Summary counts (computed from details)
    total_cutters = models.IntegerField(default=0)
    replace_count = models.IntegerField(default=0)
    repair_count = models.IntegerField(default=0)
    ok_count = models.IntegerField(default=0)
    rotate_count = models.IntegerField(default=0)
    lost_count = models.IntegerField(default=0)

    # Notes
    comments = models.TextField(
        blank=True,
        default="",
        help_text="General evaluation comments"
    )
    source_description = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Source (e.g., 'ARDT Cutter Entry', 'Eval-LSTK')"
    )

    # Override tracking
    overrides_evaluation = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='override_evaluations',
        help_text="Evaluation this overrides (for engineer overrides)"
    )

    class Meta:
        db_table = "production_job_cutter_evaluation_header"
        verbose_name = "Cutter Evaluation"
        verbose_name_plural = "Cutter Evaluations"
        ordering = ['job_card', '-revision_number']
        indexes = [
            models.Index(fields=['job_card', 'evaluation_type'], name='ix_cuteval_jc_type'),
            models.Index(fields=['status'], name='ix_cuteval_status'),
            models.Index(fields=['evaluated_by'], name='ix_cuteval_by'),
        ]

    def __str__(self):
        return f"{self.job_card.job_card_number} - {self.get_evaluation_type_display()} v{self.revision_number}"

    def calculate_summary(self):
        """Calculate summary counts from detail records."""
        from django.db.models import Count, Q

        details = self.details.all()
        self.total_cutters = details.count()

        # Count by symbol action
        self.replace_count = details.filter(
            symbol__action='REPLACE'
        ).count()
        self.repair_count = details.filter(
            symbol__action__in=['REPAIR_BRAZE', 'BUILD_UP']
        ).count()
        self.ok_count = details.filter(
            symbol__action='KEEP'
        ).count()
        self.rotate_count = details.filter(
            symbol__action='ROTATE'
        ).count()
        self.lost_count = details.filter(
            symbol__action='CLEAN'
        ).count()

        self.save(update_fields=[
            'total_cutters', 'replace_count', 'repair_count',
            'ok_count', 'rotate_count', 'lost_count', 'updated_at'
        ])

    def submit_evaluation(self):
        """Submit evaluation for review."""
        self.status = 'SUBMITTED'
        self.calculate_summary()
        self.save(update_fields=['status', 'updated_at'])

    def approve_evaluation(self, user):
        """Approve evaluation."""
        self.status = 'APPROVED'
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])


class JobCutterEvaluationDetail(AuditMixin):
    """
    Individual cutter evaluation entry.

    Records the symbol/condition for each cutter location.
    """

    header = models.ForeignKey(
        JobCutterEvaluationHeader,
        on_delete=models.CASCADE,
        related_name='details',
        help_text="Parent evaluation header"
    )

    location = models.ForeignKey(
        CutterLocation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='evaluation_details',
        help_text="Cutter location being evaluated"
    )

    # Grid position (fallback if no layout defined)
    row = models.IntegerField(
        null=True,
        blank=True,
        help_text="Row position (if no layout)"
    )
    column = models.IntegerField(
        null=True,
        blank=True,
        help_text="Column position (if no layout)"
    )

    # Evaluation result
    symbol = models.ForeignKey(
        'CutterSymbol',
        on_delete=models.PROTECT,
        related_name='evaluation_details',
        help_text="Evaluation symbol"
    )

    # Optional descriptive fields
    condition_description = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Additional condition description"
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes for this specific cutter"
    )

    # Actual cutter info (may differ from expected)
    actual_cutter_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Actual cutter type found"
    )
    actual_cutter_size = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Actual cutter size found"
    )

    # Flags
    requires_special_attention = models.BooleanField(
        default=False,
        help_text="Needs special handling or attention"
    )

    class Meta:
        db_table = "production_job_cutter_evaluation_detail"
        verbose_name = "Cutter Evaluation Detail"
        verbose_name_plural = "Cutter Evaluation Details"
        ordering = ['header', 'row', 'column']
        indexes = [
            models.Index(fields=['header', 'row', 'column'], name='ix_cutdetail_hdr_pos'),
            models.Index(fields=['symbol'], name='ix_cutdetail_symbol'),
        ]

    def __str__(self):
        pos = f"R{self.row}C{self.column}"
        if self.location and self.location.label:
            pos = self.location.label
        return f"{self.header} - {pos}: {self.symbol.symbol}"


class JobCutterEvaluationOverride(AuditMixin):
    """
    Engineer override for a specific cutter evaluation entry.

    Allows engineers to override ARDT evaluation decisions.
    """

    REASON_CHOICES = (
        ('TECHNICAL', 'Technical Decision'),
        ('COST', 'Cost Optimization'),
        ('AVAILABILITY', 'Cutter Availability'),
        ('CUSTOMER_REQUEST', 'Customer Request'),
        ('SAFETY', 'Safety Concern'),
        ('OTHER', 'Other'),
    )

    original_detail = models.ForeignKey(
        JobCutterEvaluationDetail,
        on_delete=models.CASCADE,
        related_name='overrides',
        help_text="Original evaluation entry being overridden"
    )

    original_symbol = models.ForeignKey(
        'CutterSymbol',
        on_delete=models.PROTECT,
        related_name='overridden_as_original',
        help_text="Original symbol that was overridden"
    )

    new_symbol = models.ForeignKey(
        'CutterSymbol',
        on_delete=models.PROTECT,
        related_name='overridden_as_new',
        help_text="New symbol after override"
    )

    reason_type = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        default='TECHNICAL'
    )
    reason_detail = models.TextField(
        help_text="Detailed explanation for override"
    )

    engineer = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.PROTECT,
        related_name='cutter_overrides',
        help_text="Engineer who made the override"
    )

    overridden_at = models.DateTimeField(
        default=timezone.now
    )

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_overrides',
        help_text="Supervisor who approved the override"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_approved = models.BooleanField(
        default=False,
        help_text="Override has been approved"
    )

    class Meta:
        db_table = "production_job_cutter_evaluation_override"
        verbose_name = "Cutter Evaluation Override"
        verbose_name_plural = "Cutter Evaluation Overrides"
        ordering = ['-overridden_at']
        indexes = [
            models.Index(fields=['original_detail'], name='ix_cutover_detail'),
            models.Index(fields=['engineer'], name='ix_cutover_engineer'),
        ]

    def __str__(self):
        return f"Override: {self.original_symbol.symbol} -> {self.new_symbol.symbol} by {self.engineer}"

    def approve(self, user):
        """Approve the override."""
        self.is_approved = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at', 'updated_at'])

        # Update the original detail to use the new symbol
        self.original_detail.symbol = self.new_symbol
        self.original_detail.save(update_fields=['symbol', 'updated_at'])

        # Recalculate evaluation summary
        self.original_detail.header.calculate_summary()
