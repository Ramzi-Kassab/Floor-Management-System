# Cutter BOM & Map Grid System - Complete Implementation

## Overview

This document provides the complete implementation for an Excel-like Cutter BOM and Map grid system that matches your exact requirements.

## 🎯 Requirements Summary (What You Asked For)

### Grid Features
1. ✅ Excel-like grid behavior (cell navigation, real-time updates)
2. ✅ BOM quantity validation (prevent over-entry, show counters)
3. ✅ Real-time server updates
4. ✅ Primary/secondary cutter alignment
5. ✅ Three ordering schemes (continuous, reset, formation engagement)

### Multi-Stage Usage
Same grid structure used by:
1. ✅ Technical team (design BOM upload)
2. ✅ Receiving inspector
3. ✅ Production team
4. ✅ QC (evaluations)
5. ✅ NDT (remarks)
6. ✅ Rework tracking
7. ✅ Final inspection

### Management
1. ✅ BOM version tracking
2. ✅ Usage tracking (which bits use which BOM)
3. ✅ Easy modification for testing/shortage
4. ✅ Color coding for all stages

---

## 📊 Data Model Enhancement

### 1. Cutter BOM Grid (Design Definition)

```python
# floor_app/operations/inventory/models/cutter_bom_grid.py

from django.db import models
from django.core.exceptions import ValidationError
from floor_app.mixins import AuditMixin
from decimal import Decimal


class CutterBOMGridHeader(AuditMixin):
    """
    Grid-based BOM for cutters arranged by blade and pocket.

    Replaces linear BOMLine approach with structured grid matching
    the physical layout of cutters on the bit.
    """

    ORDERING_SCHEME_CHOICES = (
        ('CONTINUOUS', 'Continuous (1 to N across all blades)'),
        ('RESET_PER_TYPE', 'Reset per Primary/Secondary'),
        ('FORMATION', 'Formation Engagement Order (apex to gauge)'),
    )

    # Links to existing BOMHeader
    bom_header = models.OneToOneField(
        'BOMHeader',
        on_delete=models.CASCADE,
        related_name='cutter_grid',
        help_text="Parent BOM header"
    )

    # Grid dimensions
    blade_count = models.PositiveIntegerField(
        help_text="Number of blades on this bit"
    )

    max_pockets_per_blade = models.PositiveIntegerField(
        help_text="Maximum pockets per blade (grid height)"
    )

    # Ordering configuration
    cutter_ordering_scheme = models.CharField(
        max_length=20,
        choices=ORDERING_SCHEME_CHOICES,
        default='CONTINUOUS',
        help_text="How cutters are numbered in this BOM"
    )

    # Layout metadata
    layout_description = models.TextField(
        blank=True,
        help_text="Description of pocket layout (e.g., 'Standard 5-blade with apex to gauge progression')"
    )

    # Total cutter counts (calculated)
    total_primary_cutters = models.PositiveIntegerField(
        default=0,
        help_text="Total primary cutters in BOM"
    )

    total_secondary_cutters = models.PositiveIntegerField(
        default=0,
        help_text="Total secondary cutters in BOM"
    )

    class Meta:
        db_table = "inventory_cutter_bom_grid_header"
        verbose_name = "Cutter BOM Grid"
        verbose_name_plural = "Cutter BOM Grids"

    def __str__(self):
        return f"Cutter Grid for {self.bom_header.bom_number}"

    def recalculate_totals(self):
        """Recalculate total cutter counts."""
        cells = self.cells.all()
        self.total_primary_cutters = cells.filter(is_primary=True, cutter_type__isnull=False).count()
        self.total_secondary_cutters = cells.filter(is_primary=False, cutter_type__isnull=False).count()
        self.save(update_fields=['total_primary_cutters', 'total_secondary_cutters'])


class CutterBOMGridCell(AuditMixin):
    """
    Individual cell in the BOM grid.

    Represents a specific pocket location that can hold a cutter.
    """

    grid_header = models.ForeignKey(
        CutterBOMGridHeader,
        on_delete=models.CASCADE,
        related_name='cells',
        help_text="Parent grid"
    )

    # Position in grid
    blade_number = models.PositiveIntegerField(
        help_text="Blade number (1-based)"
    )

    pocket_number = models.PositiveIntegerField(
        help_text="Pocket number within blade (1-based)"
    )

    is_primary = models.BooleanField(
        default=True,
        help_text="True for primary cutter, False for secondary"
    )

    # Location naming
    location_name = models.CharField(
        max_length=50,
        help_text="Location name along blade (e.g., 'Cone 1', 'Nose 2', 'Taper 1', 'Shoulder 3', 'Gauge 1')"
    )

    section = models.ForeignKey(
        'evaluation.BitSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Bit section (Cone, Nose, Taper, Shoulder, Gauge)"
    )

    # Cutter specification
    cutter_type = models.ForeignKey(
        'CutterDetail',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='bom_cells',
        help_text="Type of cutter required at this position"
    )

    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Quantity of this cutter type (usually 1)"
    )

    # Ordering/numbering
    cutter_sequence = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Cutter number in chosen ordering scheme (1 to N)"
    )

    formation_order = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Order of engagement with formation (1=apex/first contact, N=gauge/last)"
    )

    # Geometric properties
    radial_distance = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Distance from bit center (mm)"
    )

    axial_position = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Axial position along bit (mm from apex)"
    )

    # Alternative cutters
    alternative_cutter_types = models.ManyToManyField(
        'CutterDetail',
        blank=True,
        related_name='alternative_bom_cells',
        help_text="Alternative cutter types that can be used"
    )

    # Flags
    is_critical = models.BooleanField(
        default=False,
        help_text="Critical position (must not be empty)"
    )

    is_optional = models.BooleanField(
        default=False,
        help_text="Optional position (can be left empty)"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_cutter_bom_grid_cell"
        verbose_name = "BOM Grid Cell"
        verbose_name_plural = "BOM Grid Cells"
        ordering = ['grid_header', 'blade_number', 'pocket_number', 'is_primary']
        unique_together = [
            ['grid_header', 'blade_number', 'pocket_number', 'is_primary']
        ]
        indexes = [
            models.Index(fields=['grid_header', 'blade_number'], name='ix_bomcell_grid_blade'),
            models.Index(fields=['cutter_type'], name='ix_bomcell_cutter'),
            models.Index(fields=['cutter_sequence'], name='ix_bomcell_seq'),
        ]

    def __str__(self):
        p_or_s = "P" if self.is_primary else "S"
        cutter = self.cutter_type.sap_number if self.cutter_type else "Empty"
        return f"B{self.blade_number}P{self.pocket_number}{p_or_s}: {cutter}"

    @property
    def cell_reference(self):
        """Excel-like cell reference."""
        p_or_s = "P" if self.is_primary else "S"
        return f"B{self.blade_number}P{self.pocket_number}{p_or_s}"

    @property
    def display_label(self):
        """Human-readable label for UI."""
        p_or_s = "Primary" if self.is_primary else "Secondary"
        return f"Blade {self.blade_number}, Pocket {self.pocket_number} ({p_or_s}) - {self.location_name}"

    def assign_sequence_number(self):
        """
        Assign sequence number based on grid's ordering scheme.
        """
        scheme = self.grid_header.cutter_ordering_scheme

        if scheme == 'CONTINUOUS':
            # Continuous 1 to N across all blades, primary then secondary
            if self.is_primary:
                prior_count = CutterBOMGridCell.objects.filter(
                    grid_header=self.grid_header,
                    is_primary=True,
                    blade_number__lt=self.blade_number
                ).count()
                prior_count += CutterBOMGridCell.objects.filter(
                    grid_header=self.grid_header,
                    is_primary=True,
                    blade_number=self.blade_number,
                    pocket_number__lt=self.pocket_number
                ).count()
                self.cutter_sequence = prior_count + 1
            else:
                # Secondary starts after all primaries
                total_primaries = CutterBOMGridCell.objects.filter(
                    grid_header=self.grid_header,
                    is_primary=True
                ).count()
                prior_secondaries = CutterBOMGridCell.objects.filter(
                    grid_header=self.grid_header,
                    is_primary=False,
                    blade_number__lt=self.blade_number
                ).count()
                prior_secondaries += CutterBOMGridCell.objects.filter(
                    grid_header=self.grid_header,
                    is_primary=False,
                    blade_number=self.blade_number,
                    pocket_number__lt=self.pocket_number
                ).count()
                self.cutter_sequence = total_primaries + prior_secondaries + 1

        elif scheme == 'RESET_PER_TYPE':
            # Reset numbering for secondary cutters
            if self.is_primary:
                prior_count = CutterBOMGridCell.objects.filter(
                    grid_header=self.grid_header,
                    is_primary=True,
                    blade_number__lt=self.blade_number
                ).count()
                prior_count += CutterBOMGridCell.objects.filter(
                    grid_header=self.grid_header,
                    is_primary=True,
                    blade_number=self.blade_number,
                    pocket_number__lt=self.pocket_number
                ).count()
                self.cutter_sequence = prior_count + 1
            else:
                # Secondary starts from 1 again
                prior_count = CutterBOMGridCell.objects.filter(
                    grid_header=self.grid_header,
                    is_primary=False,
                    blade_number__lt=self.blade_number
                ).count()
                prior_count += CutterBOMGridCell.objects.filter(
                    grid_header=self.grid_header,
                    is_primary=False,
                    blade_number=self.blade_number,
                    pocket_number__lt=self.pocket_number
                ).count()
                self.cutter_sequence = prior_count + 1

        elif scheme == 'FORMATION':
            # Use formation_order if set, otherwise fall back to continuous
            if self.formation_order:
                self.cutter_sequence = self.formation_order
            else:
                # Fall back to continuous
                self.assign_sequence_number_continuous()

        self.save(update_fields=['cutter_sequence'])

    def assign_sequence_number_continuous(self):
        """Helper for continuous scheme."""
        prior_count = CutterBOMGridCell.objects.filter(
            grid_header=self.grid_header,
            cutter_type__isnull=False
        ).exclude(id=self.id).count()
        self.cutter_sequence = prior_count + 1


class CutterBOMSummary(models.Model):
    """
    Summary of cutter quantities by type for a BOM.

    Auto-calculated from grid cells for validation.
    """

    grid_header = models.ForeignKey(
        CutterBOMGridHeader,
        on_delete=models.CASCADE,
        related_name='summaries',
        help_text="Parent grid"
    )

    cutter_type = models.ForeignKey(
        'CutterDetail',
        on_delete=models.CASCADE,
        related_name='bom_summaries',
        help_text="Cutter type"
    )

    required_quantity = models.PositiveIntegerField(
        help_text="Total required quantity in BOM"
    )

    primary_count = models.PositiveIntegerField(
        default=0,
        help_text="Count in primary positions"
    )

    secondary_count = models.PositiveIntegerField(
        default=0,
        help_text="Count in secondary positions"
    )

    last_calculated = models.DateTimeField(
        auto_now=True,
        help_text="When this summary was last updated"
    )

    class Meta:
        db_table = "inventory_cutter_bom_summary"
        verbose_name = "Cutter BOM Summary"
        verbose_name_plural = "Cutter BOM Summaries"
        unique_together = [['grid_header', 'cutter_type']]

    def __str__(self):
        return f"{self.cutter_type.sap_number}: {self.required_quantity} required"

    @classmethod
    def refresh_for_grid(cls, grid_header):
        """
        Recalculate summaries for a grid.
        """
        from django.db.models import Count, Q

        # Delete existing summaries
        cls.objects.filter(grid_header=grid_header).delete()

        # Calculate new summaries
        cutter_counts = grid_header.cells.filter(
            cutter_type__isnull=False
        ).values('cutter_type').annotate(
            total=Count('id'),
            primaries=Count('id', filter=Q(is_primary=True)),
            secondaries=Count('id', filter=Q(is_primary=False))
        )

        for count_data in cutter_counts:
            cls.objects.create(
                grid_header=grid_header,
                cutter_type_id=count_data['cutter_type'],
                required_quantity=count_data['total'],
                primary_count=count_data['primaries'],
                secondary_count=count_data['secondaries']
            )


### 2. Cutter Map (As-Built Tracking)

class CutterMapHeader(AuditMixin):
    """
    Cutter Map tracks actual installed cutters vs BOM.

    Used by:
    - Production (track what was installed)
    - Receiving (verify incoming bit)
    - Rework (track changes)
    - Final inspection (verify completion)
    """

    MAP_TYPE_CHOICES = (
        ('DESIGN', 'Design Map (from BOM)'),
        ('AS_RECEIVED', 'As Received (incoming inspection)'),
        ('AS_BUILT', 'As Built (production)'),
        ('POST_EVAL', 'Post Evaluation (after QC)'),
        ('POST_REWORK', 'Post Rework'),
        ('FINAL', 'Final (before shipping)'),
    )

    # Links to job card
    job_card = models.ForeignKey(
        'production.JobCard',
        on_delete=models.CASCADE,
        related_name='cutter_maps',
        help_text="Job card this map belongs to"
    )

    # Map type and timing
    map_type = models.CharField(
        max_length=20,
        choices=MAP_TYPE_CHOICES,
        help_text="Type/stage of this map"
    )

    sequence_number = models.PositiveIntegerField(
        default=1,
        help_text="Sequence for multiple maps of same type (e.g., multiple reworks)"
    )

    # Source BOM
    source_bom_grid = models.ForeignKey(
        CutterBOMGridHeader,
        on_delete=models.PROTECT,
        related_name='maps',
        help_text="BOM grid this map is based on"
    )

    # Completion tracking
    is_complete = models.BooleanField(
        default=False,
        help_text="All required positions filled"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When map was marked complete"
    )

    completed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_maps',
        help_text="User who completed this map"
    )

    # Validation status
    validation_status = models.CharField(
        max_length=20,
        choices=[
            ('NOT_VALIDATED', 'Not Validated'),
            ('IN_PROGRESS', 'Validation In Progress'),
            ('PASS', 'Pass'),
            ('FAIL', 'Fail'),
        ],
        default='NOT_VALIDATED'
    )

    validation_notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_cutter_map_header"
        verbose_name = "Cutter Map"
        verbose_name_plural = "Cutter Maps"
        unique_together = [['job_card', 'map_type', 'sequence_number']]
        ordering = ['job_card', 'map_type', '-sequence_number']

    def __str__(self):
        return f"{self.job_card.job_card_number} - {self.get_map_type_display()} #{self.sequence_number}"

    def initialize_from_bom(self):
        """
        Create map cells from BOM grid.
        Called when map is first created.
        """
        for bom_cell in self.source_bom_grid.cells.all():
            CutterMapCell.objects.create(
                map_header=self,
                blade_number=bom_cell.blade_number,
                pocket_number=bom_cell.pocket_number,
                is_primary=bom_cell.is_primary,
                location_name=bom_cell.location_name,
                section=bom_cell.section,
                required_cutter_type=bom_cell.cutter_type,
                cutter_sequence=bom_cell.cutter_sequence,
                # actual_cutter_type left null (to be filled)
            )

    def validate_against_bom(self):
        """
        Validate map against BOM requirements.

        Returns dict with validation results.
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'cutter_count_ok': {},
        }

        # Check each cutter type quantity
        bom_summaries = self.source_bom_grid.summaries.all()

        for summary in bom_summaries:
            actual_count = self.cells.filter(
                actual_cutter_type=summary.cutter_type
            ).count()

            required_count = summary.required_quantity

            if actual_count > required_count:
                results['is_valid'] = False
                results['errors'].append(
                    f"{summary.cutter_type.sap_number}: {actual_count} installed, only {required_count} required"
                )
                results['cutter_count_ok'][summary.cutter_type.id] = False
            elif actual_count < required_count:
                results['warnings'].append(
                    f"{summary.cutter_type.sap_number}: {actual_count}/{required_count} installed (need {required_count - actual_count} more)"
                )
                results['cutter_count_ok'][summary.cutter_type.id] = False
            else:
                results['cutter_count_ok'][summary.cutter_type.id] = True

        return results


class CutterMapCell(AuditMixin):
    """
    Individual cell in cutter map.

    Tracks both required (from BOM) and actual (installed) cutter.
    """

    map_header = models.ForeignKey(
        CutterMapHeader,
        on_delete=models.CASCADE,
        related_name='cells',
        help_text="Parent map"
    )

    # Position (matches BOM grid)
    blade_number = models.PositiveIntegerField()
    pocket_number = models.PositiveIntegerField()
    is_primary = models.BooleanField(default=True)
    location_name = models.CharField(max_length=50)

    section = models.ForeignKey(
        'evaluation.BitSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Cutter numbering
    cutter_sequence = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Cutter number (for labeling)"
    )

    # Required vs actual
    required_cutter_type = models.ForeignKey(
        'CutterDetail',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='map_cells_required',
        help_text="Cutter type required by BOM"
    )

    actual_cutter_type = models.ForeignKey(
        'CutterDetail',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='map_cells_actual',
        help_text="Actual cutter type installed"
    )

    # Specific cutter instance (if serialized)
    actual_cutter_serial = models.ForeignKey(
        'inventory.SerialUnit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='map_cells',
        help_text="Specific serialized cutter installed (if tracked)"
    )

    # Installation details
    installed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When cutter was installed"
    )

    installed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installed_cutters',
        help_text="Who installed this cutter"
    )

    # Status and color coding
    status = models.CharField(
        max_length=20,
        choices=[
            ('EMPTY', 'Empty'),
            ('CORRECT', 'Correct (matches BOM)'),
            ('SUBSTITUTED', 'Substituted (different type)'),
            ('DAMAGED', 'Damaged'),
            ('REWORKED', 'Reworked'),
        ],
        default='EMPTY'
    )

    # Remarks from different teams
    production_notes = models.TextField(blank=True, default="")
    qc_notes = models.TextField(blank=True, default="")
    ndt_notes = models.TextField(blank=True, default="")
    rework_notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "inventory_cutter_map_cell"
        verbose_name = "Cutter Map Cell"
        verbose_name_plural = "Cutter Map Cells"
        unique_together = [['map_header', 'blade_number', 'pocket_number', 'is_primary']]
        ordering = ['map_header', 'blade_number', 'pocket_number', 'is_primary']

    def __str__(self):
        p_or_s = "P" if self.is_primary else "S"
        actual = self.actual_cutter_type.sap_number if self.actual_cutter_type else "Empty"
        return f"B{self.blade_number}P{self.pocket_number}{p_or_s}: {actual}"

    @property
    def cell_reference(self):
        """Excel-like cell reference."""
        p_or_s = "P" if self.is_primary else "S"
        return f"B{self.blade_number}P{self.pocket_number}{p_or_s}"

    @property
    def matches_bom(self):
        """Check if actual matches required."""
        if not self.required_cutter_type or not self.actual_cutter_type:
            return None
        return self.actual_cutter_type == self.required_cutter_type

    @property
    def color_code(self):
        """
        Get color code for this cell based on status.

        Returns hex color for UI rendering.
        """
        color_map = {
            'EMPTY': '#f8f9fa',  # Light gray
            'CORRECT': '#d4edda',  # Light green
            'SUBSTITUTED': '#fff3cd',  # Light yellow
            'DAMAGED': '#f8d7da',  # Light red
            'REWORKED': '#d1ecf1',  # Light blue
        }
        return color_map.get(self.status, '#ffffff')

    def update_status(self):
        """Auto-update status based on actual vs required."""
        if not self.actual_cutter_type:
            self.status = 'EMPTY'
        elif self.matches_bom:
            self.status = 'CORRECT'
        else:
            self.status = 'SUBSTITUTED'
        self.save(update_fields=['status'])


### 3. BOM Version Tracking & Usage

class BOMUsageTracking(models.Model):
    """
    Tracks which bits/jobs use which BOM version.

    Essential for:
    - Impact analysis (if we change BOM, which bits are affected?)
    - Historical tracking (what BOM was used for this specific bit?)
    - Version control (which is current, which is obsolete?)
    """

    bom_header = models.ForeignKey(
        'BOMHeader',
        on_delete=models.PROTECT,
        related_name='usage_records',
        help_text="BOM that was used"
    )

    job_card = models.ForeignKey(
        'production.JobCard',
        on_delete=models.CASCADE,
        related_name='bom_usage',
        help_text="Job card that used this BOM"
    )

    used_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this BOM was assigned to job"
    )

    used_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who assigned this BOM"
    )

    was_modified = models.BooleanField(
        default=False,
        help_text="True if BOM was modified for this specific job (e.g., shortage substitution)"
    )

    modification_notes = models.TextField(
        blank=True,
        help_text="Description of modifications made"
    )

    class Meta:
        db_table = "inventory_bom_usage_tracking"
        verbose_name = "BOM Usage Record"
        verbose_name_plural = "BOM Usage Records"
        ordering = ['-used_at']

    def __str__(self):
        return f"{self.bom_header.bom_number} used for {self.job_card.job_card_number}"
```

---

## 🎨 Color Coding System

### Stage-Based Color Codes

```python
# Color schemes for different stages

STAGE_COLORS = {
    # Design/BOM Definition
    'design': {
        'filled': '#e3f2fd',  # Light blue
        'primary': '#1976d2',  # Blue
        'secondary': '#90caf9',  # Lighter blue
        'optional': '#f5f5f5',  # Gray
        'critical': '#ffebee',  # Light red highlight
    },

    # Receiving Inspection
    'receiving': {
        'correct': '#d4edda',  # Green - matches BOM
        'substituted': '#fff3cd',  # Yellow - different type
        'damaged': '#f8d7da',  # Red - damaged on arrival
        'missing': '#f8f9fa',  # Gray - empty pocket
    },

    # Production
    'production': {
        'installed': '#d4edda',  # Green - installed correctly
        'pending': '#fff3cd',  # Yellow - pending installation
        'substituted': '#ffe0b2',  # Orange - using alternative
        'issue': '#f8d7da',  # Red - installation problem
    },

    # QC Evaluation (uses existing evaluation codes)
    'qc_evaluation': {
        'X': '#ffffff',  # White - OK
        'O': '#d4edda',  # Green - acceptable wear
        'S': '#fff3cd',  # Yellow - salvageable
        'R': '#ffe0b2',  # Orange - rotate
        'L': '#f8d7da',  # Red - lost
    },

    # NDT
    'ndt': {
        'pass': '#d4edda',  # Green - NDT pass
        'alert': '#fff3cd',  # Yellow - NDT alert
        'fail': '#f8d7da',  # Red - NDT fail
        'not_tested': '#f5f5f5',  # Gray - not tested
    },

    # Rework
    'rework': {
        'replaced': '#d1ecf1',  # Blue - replaced
        'repaired': '#e3f2fd',  # Light blue - repaired
        'no_action': '#d4edda',  # Green - no action needed
        'pending': '#fff3cd',  # Yellow - rework pending
    },

    # Final Inspection
    'final': {
        'approved': '#d4edda',  # Green - approved
        'conditional': '#fff3cd',  # Yellow - conditional
        'rejected': '#f8d7da',  # Red - rejected
    },
}


def get_cell_color(cell, stage):
    """
    Get color for a map cell based on current stage.

    Args:
        cell: CutterMapCell instance
        stage: Current workflow stage

    Returns:
        Hex color code
    """
    colors = STAGE_COLORS.get(stage, {})

    if stage == 'receiving':
        if not cell.actual_cutter_type:
            return colors.get('missing', '#f8f9fa')
        elif cell.matches_bom:
            return colors.get('correct', '#d4edda')
        elif cell.status == 'DAMAGED':
            return colors.get('damaged', '#f8d7da')
        else:
            return colors.get('substituted', '#fff3cd')

    elif stage == 'production':
        if cell.actual_cutter_type:
            if cell.matches_bom:
                return colors.get('installed', '#d4edda')
            else:
                return colors.get('substituted', '#ffe0b2')
        else:
            return colors.get('pending', '#fff3cd')

    # Add more stage-specific logic as needed

    return cell.color_code  # Fall back to cell's own color
```

---

**This is Part 1 of the implementation. Shall I continue with:**
- Part 2: Real-time validation logic
- Part 3: Frontend grid component (Excel-like behavior)
- Part 4: API endpoints and WebSocket updates
- Part 5: Management commands and test data?

Which part would you like me to focus on next?
