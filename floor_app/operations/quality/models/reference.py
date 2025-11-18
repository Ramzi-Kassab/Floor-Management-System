"""
Quality Management - Reference Tables
Defect categories, root cause categories, and acceptance criteria templates.
"""
from django.db import models
from floor_app.mixins import PublicIdMixin, AuditMixin, SoftDeleteMixin


class DefectCategory(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Classification of quality issues.
    Used for categorizing NCRs and defects found during inspection.
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Short code (e.g., VISUAL, DIMENSIONAL, MATERIAL)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    is_critical = models.BooleanField(
        default=False,
        help_text="Critical defects trigger immediate containment"
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "quality_defect_category"
        verbose_name = "Defect Category"
        verbose_name_plural = "Defect Categories"
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['code'], name='ix_qual_defcat_code'),
            models.Index(fields=['is_critical'], name='ix_qual_defcat_critical'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class RootCauseCategory(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Categories for root cause analysis (5-Why / Ishikawa).
    Standard categories: Man, Machine, Method, Material, Measurement, Environment.
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Category code (e.g., MAN, MACHINE, METHOD)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "quality_root_cause_category"
        verbose_name = "Root Cause Category"
        verbose_name_plural = "Root Cause Categories"
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['code'], name='ix_qual_rccat_code'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class AcceptanceCriteriaTemplate(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Reusable quality standards and acceptance criteria templates.
    Can be specific to bit type, customer, or process.
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Template code (e.g., ARAMCO-HDBS-GRINDING)"
    )
    name = models.CharField(max_length=200)
    description = models.TextField()

    # Applicability filters
    applies_to_bit_type = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Bit type code (e.g., HDBS, SMI, PDC)"
    )
    applies_to_customer = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Customer name or code (e.g., ARAMCO)"
    )
    applies_to_process = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Process name (e.g., GRINDING, BRAZING, THREADING)"
    )

    # Criteria specifications (flexible JSON structure)
    criteria_json = models.JSONField(
        default=dict,
        help_text="Criteria values as JSON (e.g., {\"max_wear_flat\": 3.0, \"min_exposure\": 2.5})"
    )

    # Standard references
    api_standard = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="API standard reference (e.g., API RP 7G-2)"
    )
    customer_spec = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Customer specification reference"
    )
    internal_spec = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Internal specification/procedure reference"
    )

    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default="1.0")

    class Meta:
        db_table = "quality_acceptance_criteria_template"
        verbose_name = "Acceptance Criteria Template"
        verbose_name_plural = "Acceptance Criteria Templates"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code'], name='ix_qual_actempl_code'),
            models.Index(
                fields=['applies_to_bit_type', 'applies_to_customer'],
                name='ix_qual_actempl_bit_cust'
            ),
            models.Index(fields=['is_active'], name='ix_qual_actempl_active'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_criterion(self, key, default=None):
        """Get a specific criterion value from the JSON."""
        return self.criteria_json.get(key, default)
