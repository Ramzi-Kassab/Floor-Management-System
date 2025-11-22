"""
Bit Design Layer - MAT Number and Type Management

This module handles the design identification system for PDC bits:
- BitDesignLevel: L3 (head only), L4 (body no cutters), L5 (complete)
- BitDesignType: HDBS, SMI, and other design families
- BitDesign: Conceptual design family
- BitDesignRevision: Specific MAT number with revision (THE KEY IDENTIFIER)
"""

from django.db import models
from floor_app.mixins import AuditMixin, SoftDeleteMixin, PublicIdMixin


class BitDesignLevel(models.Model):
    """
    PDC Bit design levels representing different stages of design completeness.

    L3 = Bit Head Only (cutting structure/blade geometry)
    L4 = Bit Body + Upper Section (no cutters)
    L5 = Complete Bit Assembly (head + body + cutters + all components)
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Level code (e.g., L3, L4, L5)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable name"
    )
    description = models.TextField(
        help_text="Detailed description of what this level includes"
    )
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'inventory'
        db_table = "inventory_bit_design_level"
        verbose_name = "Bit Design Level"
        verbose_name_plural = "Bit Design Levels"
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class BitDesignType(models.Model):
    """
    Design families or customer-specific types.

    Examples: HDBS Type, SMI Type, etc.
    Type can change based on cutter configuration or retrofit.
    """
    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Type code (e.g., HDBS, SMI)"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'inventory'
        db_table = "inventory_bit_design_type"
        verbose_name = "Bit Design Type"
        verbose_name_plural = "Bit Design Types"
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class BitDesign(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Conceptual bit design (family/base), regardless of specific revision.

    This represents the core design concept before any revisions.
    Think of it as the "product family" - multiple revisions (MATs) can
    belong to the same BitDesign.

    Example: HP-X123 is the design; HP-X123-M0, HP-X123-M1 are revisions.
    """
    design_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Internal design code (e.g., HP-X123)"
    )
    name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Descriptive name for the design"
    )
    level = models.ForeignKey(
        BitDesignLevel,
        on_delete=models.PROTECT,
        related_name='designs',
        help_text="Design level (L3/L4/L5)"
    )

    # Common design attributes (fixed, not EAV for performance)
    size_inches = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Bit size in inches (e.g., 8.50, 12.25)"
    )
    connection_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Connection type (e.g., 4-1/2 API REG, 6-5/8 REG)"
    )
    blade_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of blades"
    )
    total_cutter_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total number of cutters for L5 designs"
    )

    # Additional attributes
    nozzle_count = models.IntegerField(null=True, blank=True)
    tfa_range = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Total Flow Area range"
    )

    description = models.TextField(blank=True, default="")

    class Meta:
        app_label = 'inventory'
        db_table = "inventory_bit_design"
        verbose_name = "Bit Design"
        verbose_name_plural = "Bit Designs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['design_code'], name='ix_bd_design_code'),
            models.Index(fields=['level', 'size_inches'], name='ix_bd_level_size'),
        ]

    def __str__(self):
        return f"{self.design_code} ({self.level.code})"

    @property
    def current_revision(self):
        """Get the latest active revision for this design."""
        return self.revisions.filter(
            is_active=True, is_temporary=False
        ).order_by('-effective_date', '-created_at').first()


class BitDesignRevision(PublicIdMixin, AuditMixin, SoftDeleteMixin):
    """
    Specific MAT number at a specific revision - THE PRIMARY DESIGN IDENTIFIER.

    This is what gets linked to Items, BOMs, and SerialUnits.

    Key features:
    - mat_number: Full MAT identifier (e.g., HP-X123-M2)
    - revision_code: Version within the design (M0, M1, M2...)
    - is_temporary: For temporary MATs before official L5 is assigned
    - superseded_by: Links to newer revision when this one is replaced

    MAT numbers can change during retrofit, testing, or cutter shortage.
    The system must support:
    - Global supersession (old MAT replaced everywhere)
    - Serial-specific MAT variants (MAT-SN format)
    """
    mat_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Full MAT number (e.g., HP-X123-M2, HP-X123-SN12345)"
    )
    bit_design = models.ForeignKey(
        BitDesign,
        on_delete=models.PROTECT,
        related_name='revisions',
        help_text="Parent conceptual design"
    )
    revision_code = models.CharField(
        max_length=20,
        help_text="Revision identifier within the design (e.g., M0, M1, M2)"
    )
    design_type = models.ForeignKey(
        BitDesignType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='revisions',
        help_text="Design family/type (can be overridden per revision)"
    )

    # Revision status
    is_temporary = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if this is a temporary MAT (pending official L5)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="False when superseded or obsoleted"
    )

    # Supersession chain
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes',
        help_text="Newer revision that replaces this one"
    )

    # Dates
    effective_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this revision becomes effective"
    )
    obsolete_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this revision was obsoleted"
    )

    # Change tracking
    change_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for this revision (ECN reference, design change, etc.)"
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = 'inventory'
        db_table = "inventory_bit_design_revision"
        verbose_name = "Bit Design Revision (MAT)"
        verbose_name_plural = "Bit Design Revisions (MATs)"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['bit_design', 'revision_code'],
                name='uq_bdr_design_revision'
            ),
        ]
        indexes = [
            models.Index(fields=['mat_number'], name='ix_bdr_mat_number'),
            models.Index(fields=['bit_design', 'is_active'], name='ix_bdr_design_active'),
            models.Index(fields=['design_type'], name='ix_bdr_design_type'),
            models.Index(fields=['is_temporary', 'is_active'], name='ix_bdr_temp_active'),
        ]

    def __str__(self):
        status = ""
        if self.is_temporary:
            status = " [TEMP]"
        if not self.is_active:
            status = " [OBSOLETE]"
        return f"{self.mat_number}{status}"

    @property
    def full_designation(self):
        """Returns full designation including type if available."""
        type_str = f" ({self.design_type.code})" if self.design_type else ""
        return f"{self.mat_number}{type_str}"

    @property
    def is_superseded(self):
        """Check if this revision has been superseded."""
        return self.superseded_by is not None

    @property
    def level(self):
        """Convenience property to get the design level."""
        return self.bit_design.level

    def supersede_with(self, new_revision):
        """
        Mark this revision as superseded by a new one.

        Args:
            new_revision: BitDesignRevision instance that replaces this one
        """
        from django.utils import timezone
        self.superseded_by = new_revision
        self.is_active = False
        self.obsolete_date = timezone.now().date()
        self.save(update_fields=['superseded_by', 'is_active', 'obsolete_date', 'updated_at'])
