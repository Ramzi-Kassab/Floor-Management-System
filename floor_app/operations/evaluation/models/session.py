"""
Core Evaluation Session Model

The main container for a complete bit evaluation, linking to the physical
serial unit, MAT design, and job context. Tracks evaluation workflow status.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class EvaluationSession(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Represents a single evaluation of a PDC bit.

    This is the central model for evaluation data, containing:
    - Link to the physical bit (SerialUnit)
    - Reference MAT design used for evaluation
    - Context of evaluation (new bit, after run, repair intake, etc.)
    - Workflow status (draft, review, approved, locked)
    - Summary statistics of evaluation results
    """

    CONTEXT_CHOICES = (
        ('NEW_BIT', 'New Bit Production'),
        ('AFTER_RUN', 'After Run Evaluation'),
        ('REPAIR_INTAKE', 'Repair Intake'),
        ('POST_REPAIR', 'Post-Repair Verification'),
        ('RECLAIM_ONLY', 'Reclaim/Salvage Only'),
        ('RETROFIT_INTENT', 'Retrofit Intent Evaluation'),
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('LOCKED', 'Locked'),
    )

    # Core relationships
    serial_unit = models.ForeignKey(
        'inventory.SerialUnit',
        on_delete=models.PROTECT,
        related_name='evaluation_sessions',
        help_text="The physical bit being evaluated"
    )

    mat_revision = models.ForeignKey(
        'inventory.BitDesignRevision',
        on_delete=models.PROTECT,
        related_name='evaluation_sessions',
        help_text="MAT/design revision used as reference for this evaluation"
    )

    job_card = models.ForeignKey(
        'production.JobCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluation_sessions',
        help_text="Associated job card (if applicable)"
    )

    batch_order = models.ForeignKey(
        'production.BatchOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluation_sessions',
        help_text="Associated batch order (if applicable)"
    )

    # Context and classification
    context = models.CharField(
        max_length=30,
        choices=CONTEXT_CHOICES,
        default='REPAIR_INTAKE',
        db_index=True,
        help_text="Context/purpose of this evaluation"
    )

    customer_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Customer name (denormalized for quick access)"
    )

    project_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Project/well/field name"
    )

    # Workflow status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True,
        help_text="Current workflow status of the evaluation"
    )

    # Personnel
    evaluator = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.PROTECT,
        related_name='evaluations_conducted',
        help_text="Employee who performed the evaluation"
    )

    reviewing_engineer = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluations_reviewed',
        help_text="Engineer who reviewed/approved the evaluation"
    )

    # Workflow timestamps
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When evaluation was submitted for review"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When evaluation was approved"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluations_approved',
        help_text="User who approved the evaluation"
    )

    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When evaluation was locked (no further changes)"
    )

    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluations_locked',
        help_text="User who locked the evaluation"
    )

    # State tracking
    is_last_known_state = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if this is the most recent evaluation for the serial unit"
    )

    # Summary statistics (denormalized for performance)
    total_cells = models.IntegerField(
        default=0,
        help_text="Total number of cells evaluated"
    )

    replace_count = models.IntegerField(
        default=0,
        help_text="Number of cutters marked for replacement (X code)"
    )

    ok_count = models.IntegerField(
        default=0,
        help_text="Number of cutters marked as OK (O code)"
    )

    braze_count = models.IntegerField(
        default=0,
        help_text="Number of cutters needing braze fill (S code)"
    )

    rotate_count = models.IntegerField(
        default=0,
        help_text="Number of cutters to rotate (R code)"
    )

    lost_count = models.IntegerField(
        default=0,
        help_text="Number of cutters lost/missing (L code)"
    )

    # Additional notes
    general_notes = models.TextField(
        blank=True,
        default="",
        help_text="General notes about the evaluation"
    )

    wear_pattern_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes about observed wear patterns"
    )

    damage_assessment = models.TextField(
        blank=True,
        default="",
        help_text="Overall damage assessment"
    )

    recommendations = models.TextField(
        blank=True,
        default="",
        help_text="Recommendations for repair/action"
    )

    class Meta:
        db_table = "evaluation_session"
        verbose_name = "Evaluation Session"
        verbose_name_plural = "Evaluation Sessions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['serial_unit', '-created_at'], name='ix_eval_serial_created'),
            models.Index(fields=['status', '-created_at'], name='ix_eval_status_created'),
            models.Index(fields=['context', 'status'], name='ix_eval_context_status'),
            models.Index(fields=['evaluator', '-created_at'], name='ix_eval_evaluator'),
            models.Index(fields=['customer_name', 'status'], name='ix_eval_customer_status'),
            models.Index(fields=['is_last_known_state', 'serial_unit'], name='ix_eval_last_state'),
            models.Index(fields=['job_card'], name='ix_eval_job_card'),
            models.Index(fields=['batch_order'], name='ix_eval_batch'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_cells__gte=0),
                name='ck_eval_total_cells_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(replace_count__gte=0),
                name='ck_eval_replace_count_non_negative'
            ),
        ]

    def __str__(self):
        return f"Eval-{self.public_id.hex[:8]} ({self.serial_unit.serial_number})"

    @property
    def is_editable(self):
        """Check if evaluation can still be edited."""
        return self.status in ('DRAFT', 'UNDER_REVIEW')

    @property
    def is_locked(self):
        """Check if evaluation is locked."""
        return self.status == 'LOCKED'

    @property
    def damage_percentage(self):
        """Calculate percentage of cutters needing action."""
        if self.total_cells == 0:
            return 0
        action_needed = self.replace_count + self.braze_count + self.rotate_count + self.lost_count
        return round((action_needed / self.total_cells) * 100, 2)

    @property
    def health_score(self):
        """Calculate bit health score (percentage of OK cutters)."""
        if self.total_cells == 0:
            return 100
        return round((self.ok_count / self.total_cells) * 100, 2)

    def submit_for_review(self, user=None):
        """Submit evaluation for engineering review."""
        self.status = 'UNDER_REVIEW'
        self.submitted_at = timezone.now()
        self.save(update_fields=['status', 'submitted_at', 'updated_at'])

    def approve(self, user=None, engineer=None):
        """Approve the evaluation."""
        self.status = 'APPROVED'
        self.approved_at = timezone.now()
        self.approved_by = user
        if engineer:
            self.reviewing_engineer = engineer
        self.save(update_fields=['status', 'approved_at', 'approved_by', 'reviewing_engineer', 'updated_at'])

    def lock(self, user=None):
        """Lock the evaluation to prevent further changes."""
        self.status = 'LOCKED'
        self.locked_at = timezone.now()
        self.locked_by = user
        self.save(update_fields=['status', 'locked_at', 'locked_by', 'updated_at'])

    def revert_to_draft(self):
        """Revert evaluation back to draft status."""
        if self.status != 'LOCKED':
            self.status = 'DRAFT'
            self.submitted_at = None
            self.approved_at = None
            self.approved_by = None
            self.save(update_fields=['status', 'submitted_at', 'approved_at', 'approved_by', 'updated_at'])

    def update_summary_counts(self):
        """
        Recalculate summary counts from evaluation cells.
        Call this after modifying cells.
        """
        from django.db.models import Count, Q

        cells = self.cells.all()
        self.total_cells = cells.count()

        # Count by cutter code action
        code_counts = cells.exclude(cutter_code__isnull=True).values(
            'cutter_code__action'
        ).annotate(count=Count('id'))

        action_map = {item['cutter_code__action']: item['count'] for item in code_counts}

        self.replace_count = action_map.get('REPLACE', 0)
        self.ok_count = action_map.get('KEEP', 0)
        self.braze_count = action_map.get('BRAZE_FILL', 0)
        self.rotate_count = action_map.get('ROTATE', 0)
        self.lost_count = action_map.get('LOST', 0)

        self.save(update_fields=[
            'total_cells', 'replace_count', 'ok_count',
            'braze_count', 'rotate_count', 'lost_count', 'updated_at'
        ])

    def mark_as_latest(self):
        """Mark this as the latest evaluation for the serial unit."""
        # Clear previous latest
        EvaluationSession.objects.filter(
            serial_unit=self.serial_unit,
            is_last_known_state=True
        ).exclude(pk=self.pk).update(is_last_known_state=False)

        # Set this as latest
        self.is_last_known_state = True
        self.save(update_fields=['is_last_known_state', 'updated_at'])
