"""
Evaluation Cell Model

Represents individual cutter positions on the bit face, each evaluated
with a specific code and optional feature indicators.
"""

from django.db import models


class EvaluationCell(models.Model):
    """
    Represents a single evaluation cell (cutter position) on the bit.

    Each cell corresponds to a specific location on the bit face:
    - Blade/row number
    - Section (cone, nose, taper, shoulder, gauge)
    - Position index within the section
    - Primary or secondary cutter indicator

    The cell stores:
    - The cutter design (Item) installed at that position
    - The evaluation code (X, O, S, R, L)
    - Feature flags (fin build-up, pocket damage, etc.)
    - Geometric attributes (pocket diameter, depth)
    """

    # Parent evaluation session
    evaluation_session = models.ForeignKey(
        'EvaluationSession',
        on_delete=models.CASCADE,
        related_name='cells',
        help_text="Parent evaluation session"
    )

    # Position identification
    blade_number = models.PositiveIntegerField(
        help_text="Blade/row number (1-based)"
    )

    section = models.ForeignKey(
        'BitSection',
        on_delete=models.PROTECT,
        related_name='evaluation_cells',
        help_text="Bit section (cone, nose, taper, shoulder, gauge)"
    )

    position_index = models.PositiveIntegerField(
        help_text="Position index within the section (1-based)"
    )

    is_primary = models.BooleanField(
        default=True,
        help_text="True if primary cutter, False if secondary/backup cutter"
    )

    # Cutter information
    cutter_item = models.ForeignKey(
        'inventory.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluation_cells',
        help_text="Cutter design/item installed at this position"
    )

    # Evaluation result
    cutter_code = models.ForeignKey(
        'CutterEvaluationCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluation_cells',
        help_text="Evaluation code assigned to this cutter"
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="Specific notes for this cell/cutter"
    )

    # Feature flags (for V, P, I, B codes)
    has_fin_build_up = models.BooleanField(
        default=False,
        help_text="V code: Material build-up on fin geometry"
    )

    fin_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="If has_fin_build_up, which fin number is affected"
    )

    has_pocket_damage = models.BooleanField(
        default=False,
        help_text="P code: Damage to cutter pocket"
    )

    has_impact_arrestor_issue = models.BooleanField(
        default=False,
        help_text="I code: Issue with impact arrestor"
    )

    has_body_build_up = models.BooleanField(
        default=False,
        help_text="B code: Material build-up on bit body"
    )

    # Geometric attributes
    pocket_diameter = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Measured pocket diameter (mm)"
    )

    pocket_depth = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Measured pocket depth (mm)"
    )

    # Additional measurements
    cutter_exposure = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Cutter exposure above pocket (mm)"
    )

    wear_flat_length = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Length of wear flat on cutter (mm)"
    )

    back_rake_angle = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Back rake angle (degrees)"
    )

    side_rake_angle = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Side rake angle (degrees)"
    )

    # Tracking
    evaluated_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this cell was evaluated"
    )

    last_modified_at = models.DateTimeField(
        auto_now=True,
        help_text="When this cell was last modified"
    )

    class Meta:
        db_table = "evaluation_cell"
        verbose_name = "Evaluation Cell"
        verbose_name_plural = "Evaluation Cells"
        ordering = ['evaluation_session', 'blade_number', 'section__sequence', 'position_index']
        indexes = [
            models.Index(
                fields=['evaluation_session', 'blade_number', 'section'],
                name='ix_eval_cell_session_blade'
            ),
            models.Index(
                fields=['evaluation_session', 'cutter_code'],
                name='ix_eval_cell_session_code'
            ),
            models.Index(
                fields=['cutter_item'],
                name='ix_eval_cell_cutter_item'
            ),
            models.Index(
                fields=['section', 'is_primary'],
                name='ix_eval_cell_section_primary'
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['evaluation_session', 'blade_number', 'section', 'position_index', 'is_primary'],
                name='uq_eval_cell_position'
            ),
            models.CheckConstraint(
                check=models.Q(blade_number__gte=1),
                name='ck_eval_cell_blade_positive'
            ),
            models.CheckConstraint(
                check=models.Q(position_index__gte=1),
                name='ck_eval_cell_position_positive'
            ),
        ]

    def __str__(self):
        code_str = self.cutter_code.code if self.cutter_code else "N/A"
        primary_str = "P" if self.is_primary else "S"
        return f"B{self.blade_number}-{self.section.code}-{self.position_index}{primary_str}: {code_str}"

    @property
    def position_label(self):
        """Human-readable position label."""
        primary_str = "Primary" if self.is_primary else "Secondary"
        return f"Blade {self.blade_number}, {self.section.name}, Position {self.position_index} ({primary_str})"

    @property
    def requires_action(self):
        """Check if this cell requires repair action."""
        if not self.cutter_code:
            return False
        return self.cutter_code.action in ('REPLACE', 'BRAZE_FILL', 'ROTATE', 'LOST')

    @property
    def has_features(self):
        """Check if any feature flags are set."""
        return any([
            self.has_fin_build_up,
            self.has_pocket_damage,
            self.has_impact_arrestor_issue,
            self.has_body_build_up
        ])

    @property
    def feature_codes(self):
        """Return list of feature codes present."""
        codes = []
        if self.has_fin_build_up:
            codes.append('V')
        if self.has_pocket_damage:
            codes.append('P')
        if self.has_impact_arrestor_issue:
            codes.append('I')
        if self.has_body_build_up:
            codes.append('B')
        return codes

    def copy_from(self, source_cell):
        """Copy evaluation data from another cell (for templates)."""
        self.cutter_code = source_cell.cutter_code
        self.cutter_item = source_cell.cutter_item
        self.has_fin_build_up = source_cell.has_fin_build_up
        self.fin_number = source_cell.fin_number
        self.has_pocket_damage = source_cell.has_pocket_damage
        self.has_impact_arrestor_issue = source_cell.has_impact_arrestor_issue
        self.has_body_build_up = source_cell.has_body_build_up
        self.pocket_diameter = source_cell.pocket_diameter
        self.pocket_depth = source_cell.pocket_depth
        self.notes = source_cell.notes
