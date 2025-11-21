"""
Cutter BOM & Map Grid System

Excel-like grid for managing cutter BOMs and tracking as-built maps across
production stages with real-time availability tracking and validation.

Features:
- Grid-based BOM (blade × pocket × primary/secondary)
- Three ordering schemes (continuous, reset per type, formation engagement)
- Multi-stage tracking (design, receiving, production, QC, NDT, rework, final)
- Real-time BOM quantity validation
- Smart availability display with reclaimed cutter filtering
- Color coding for all stages
- Version tracking and usage history
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q, Count
from django.utils import timezone
from decimal import Decimal

from floor_app.mixins import AuditMixin, SoftDeleteMixin


class CutterBOMGridHeader(AuditMixin):
    """
    Grid-based BOM header for cutters arranged by blade and pocket.

    This represents the design specification - what cutters should be installed
    where, with support for different ordering schemes.
    """

    ORDERING_SCHEME_CHOICES = (
        ('CONTINUOUS', 'Continuous (1 to N across all blades)'),
        ('RESET_PER_TYPE', 'Reset per Primary/Secondary'),
        ('FORMATION', 'Formation Engagement Order (apex to gauge)'),
    )

    # Link to traditional BOM
    bom_header = models.OneToOneField(
        'engineering.BOMHeader',
        on_delete=models.CASCADE,
        related_name='cutter_grid',
        help_text="Parent BOM header"
    )

    # Grid dimensions
    blade_count = models.PositiveIntegerField(
        help_text="Number of blades on this bit"
    )
    max_pockets_per_blade = models.PositiveIntegerField(
        help_text="Maximum pockets in any blade"
    )

    # Ordering configuration
    cutter_ordering_scheme = models.CharField(
        max_length=20,
        choices=ORDERING_SCHEME_CHOICES,
        default='CONTINUOUS',
        help_text="How to number cutters in the grid"
    )

    # Auto-calculated totals
    total_primary_cutters = models.PositiveIntegerField(
        default=0,
        help_text="Total primary cutters in grid"
    )
    total_secondary_cutters = models.PositiveIntegerField(
        default=0,
        help_text="Total secondary cutters in grid"
    )

    # Availability filtering options
    show_reclaimed_cutters = models.BooleanField(
        default=False,
        help_text="Show reclaimed cutters in availability (typically False for new bits)"
    )

    class Meta:
        db_table = 'inventory_cutter_bom_grid_header'
        verbose_name = 'Cutter BOM Grid Header'
        verbose_name_plural = 'Cutter BOM Grid Headers'
        indexes = [
            models.Index(fields=['bom_header']),
        ]

    def __str__(self):
        return f"Grid for {self.bom_header.bom_number} ({self.blade_count}B × {self.max_pockets_per_blade}P)"

    def recalculate_totals(self):
        """Recalculate total primary and secondary cutter counts."""
        cells = self.cells.filter(cutter_type__isnull=False)

        self.total_primary_cutters = cells.filter(is_primary=True).count()
        self.total_secondary_cutters = cells.filter(is_primary=False).count()
        self.save(update_fields=['total_primary_cutters', 'total_secondary_cutters'])

    def refresh_summaries(self):
        """Refresh BOM summary for validation."""
        CutterBOMSummary.refresh_for_grid(self)

    def assign_all_sequence_numbers(self):
        """Assign sequence numbers to all cells based on ordering scheme."""
        if self.cutter_ordering_scheme == 'CONTINUOUS':
            self._assign_continuous_sequence()
        elif self.cutter_ordering_scheme == 'RESET_PER_TYPE':
            self._assign_reset_per_type_sequence()
        elif self.cutter_ordering_scheme == 'FORMATION':
            self._assign_formation_sequence()

    def _assign_continuous_sequence(self):
        """Assign continuous numbering 1 to N across all blades."""
        sequence = 1

        # Order by blade, then primary first, then pocket
        cells = self.cells.filter(cutter_type__isnull=False).order_by(
            'blade_number',
            '-is_primary',  # Primary first (True > False)
            'pocket_number'
        )

        for cell in cells:
            cell.cutter_sequence = sequence
            cell.save(update_fields=['cutter_sequence'])
            sequence += 1

    def _assign_reset_per_type_sequence(self):
        """Assign sequence numbers, resetting when switching from primary to secondary."""
        # Primary cutters: 1 to N
        primary_cells = self.cells.filter(
            cutter_type__isnull=False,
            is_primary=True
        ).order_by('blade_number', 'pocket_number')

        sequence = 1
        for cell in primary_cells:
            cell.cutter_sequence = sequence
            cell.save(update_fields=['cutter_sequence'])
            sequence += 1

        # Secondary cutters: restart at 1
        secondary_cells = self.cells.filter(
            cutter_type__isnull=False,
            is_primary=False
        ).order_by('blade_number', 'pocket_number')

        sequence = 1
        for cell in secondary_cells:
            cell.cutter_sequence = sequence
            cell.save(update_fields=['cutter_sequence'])
            sequence += 1

    def _assign_formation_sequence(self):
        """Assign sequence based on formation_order (apex to gauge)."""
        cells = self.cells.filter(
            cutter_type__isnull=False,
            formation_order__isnull=False
        ).order_by('formation_order')

        sequence = 1
        for cell in cells:
            cell.cutter_sequence = sequence
            cell.save(update_fields=['cutter_sequence'])
            sequence += 1

    def get_availability_summary(self):
        """
        Get smart availability summary for all cutter types in this BOM.

        Returns dict with cutter type availability, filtered by reclaimed setting.
        """
        from floor_app.operations.inventory.models import CutterInventorySummary

        # Get all cutter types in this BOM
        cutter_types = self.cells.filter(
            cutter_type__isnull=False
        ).values_list('cutter_type_id', flat=True).distinct()

        availability = {}

        for cutter_type_id in cutter_types:
            # Get summary for this cutter type
            summary = CutterInventorySummary.objects.filter(
                cutter_detail_id=cutter_type_id
            ).first()

            if summary:
                # Calculate available quantity based on reclaimed filter
                if self.show_reclaimed_cutters:
                    # Show all: new + reclaimed
                    available = summary.quantity_new_good + summary.quantity_reclaimed_good
                else:
                    # Only new cutters
                    available = summary.quantity_new_good

                availability[cutter_type_id] = {
                    'cutter_type': summary.cutter_detail,
                    'available_new': summary.quantity_new_good,
                    'available_reclaimed': summary.quantity_reclaimed_good,
                    'total_available': available,
                    'in_transit': summary.quantity_in_transit,
                    'reserved': summary.quantity_reserved,
                    'damaged': summary.quantity_damaged,
                }

        return availability


class CutterBOMGridCell(AuditMixin):
    """
    Individual cell in the BOM grid.

    Each cell represents a pocket position that can hold a cutter.
    Cells are arranged in a blade × pocket × primary/secondary structure.
    """

    grid_header = models.ForeignKey(
        CutterBOMGridHeader,
        on_delete=models.CASCADE,
        related_name='cells'
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
        help_text="Primary cutter (True) or Secondary/backup cutter (False)"
    )

    # Location information
    location_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Location name (e.g., 'Cone 1', 'Nose 2', 'Gauge 3')"
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
        help_text="Required cutter type for this position"
    )

    # Sequencing
    cutter_sequence = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Sequence number based on ordering scheme"
    )
    formation_order = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Formation engagement order (for FORMATION ordering scheme)"
    )

    # Design notes
    notes = models.TextField(
        blank=True,
        help_text="Design notes for this position"
    )

    class Meta:
        db_table = 'inventory_cutter_bom_grid_cell'
        verbose_name = 'Cutter BOM Grid Cell'
        verbose_name_plural = 'Cutter BOM Grid Cells'
        unique_together = [
            ('grid_header', 'blade_number', 'pocket_number', 'is_primary')
        ]
        indexes = [
            models.Index(fields=['grid_header', 'blade_number']),
            models.Index(fields=['grid_header', 'cutter_type']),
            models.Index(fields=['cutter_sequence']),
        ]
        ordering = ['blade_number', '-is_primary', 'pocket_number']

    def __str__(self):
        return f"{self.cell_reference}: {self.cutter_type or 'Empty'}"

    @property
    def cell_reference(self):
        """Excel-like cell reference (e.g., 'B1P3P' or 'B2P5S')."""
        p_or_s = "P" if self.is_primary else "S"
        return f"B{self.blade_number}P{self.pocket_number}{p_or_s}"

    def get_availability(self):
        """
        Get availability for this cell's cutter type.

        Returns dict with availability info respecting the grid's reclaimed filter.
        """
        if not self.cutter_type:
            return None

        availability_summary = self.grid_header.get_availability_summary()
        return availability_summary.get(self.cutter_type_id)

    def save(self, *args, **kwargs):
        """Override save to trigger summary refresh."""
        super().save(*args, **kwargs)

        # Trigger summary refresh if cutter type changed
        if self.cutter_type:
            self.grid_header.refresh_summaries()


class CutterBOMSummary(models.Model):
    """
    Auto-calculated summary of cutter quantities by type for validation.

    This table is used for real-time validation when entering cutters in the map.
    It shows: required quantity, how many entered, how many remaining.
    """

    grid_header = models.ForeignKey(
        CutterBOMGridHeader,
        on_delete=models.CASCADE,
        related_name='summaries'
    )
    cutter_type = models.ForeignKey(
        'CutterDetail',
        on_delete=models.CASCADE,
        related_name='bom_summaries'
    )

    # Required quantities (from BOM cells)
    required_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Total required quantity in BOM"
    )
    primary_count = models.PositiveIntegerField(
        default=0,
        help_text="Count as primary cutters"
    )
    secondary_count = models.PositiveIntegerField(
        default=0,
        help_text="Count as secondary cutters"
    )

    # Auto-update timestamp
    last_calculated = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'inventory_cutter_bom_summary'
        verbose_name = 'Cutter BOM Summary'
        verbose_name_plural = 'Cutter BOM Summaries'
        unique_together = [('grid_header', 'cutter_type')]
        indexes = [
            models.Index(fields=['grid_header', 'cutter_type']),
        ]

    def __str__(self):
        return f"{self.cutter_type} in {self.grid_header}: {self.required_quantity} required"

    @classmethod
    def refresh_for_grid(cls, grid_header):
        """
        Recalculate summaries for a grid.

        This is called whenever cells are added/removed/changed.
        """
        from django.db.models import Count, Q

        # Get aggregated counts by cutter type
        cell_counts = grid_header.cells.filter(
            cutter_type__isnull=False
        ).values('cutter_type').annotate(
            total=Count('id'),
            primary=Count('id', filter=Q(is_primary=True)),
            secondary=Count('id', filter=Q(is_primary=False))
        )

        # Clear existing summaries
        cls.objects.filter(grid_header=grid_header).delete()

        # Create new summaries
        summaries = []
        for counts in cell_counts:
            summaries.append(
                cls(
                    grid_header=grid_header,
                    cutter_type_id=counts['cutter_type'],
                    required_quantity=counts['total'],
                    primary_count=counts['primary'],
                    secondary_count=counts['secondary']
                )
            )

        # Bulk create
        if summaries:
            cls.objects.bulk_create(summaries)

        return summaries

    def get_remaining_for_map(self, map_header):
        """
        Calculate how many more of this cutter type are needed in a map.

        Returns:
            int: Positive = still need, Negative = over-entered, 0 = perfect
        """
        # Count how many of this type are in the map
        entered_count = map_header.cells.filter(
            actual_cutter_type=self.cutter_type
        ).count()

        remaining = self.required_quantity - entered_count
        return remaining


class CutterMapHeader(AuditMixin):
    """
    Cutter Map tracks actual installed cutters vs BOM design.

    Multiple maps exist for different stages:
    - Design map (copied from BOM)
    - As-received (incoming inspection)
    - As-built (production)
    - Post-evaluation (QC)
    - Post-rework
    - Final (before shipping)
    """

    MAP_TYPE_CHOICES = (
        ('DESIGN', 'Design Map (from BOM)'),
        ('AS_RECEIVED', 'As Received (incoming inspection)'),
        ('AS_BUILT', 'As Built (production)'),
        ('POST_EVAL', 'Post Evaluation (after QC)'),
        ('POST_NDT', 'Post NDT Inspection'),
        ('POST_REWORK', 'Post Rework'),
        ('FINAL', 'Final (before shipping)'),
    )

    VALIDATION_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('VALID', 'Valid (matches BOM)'),
        ('HAS_SUBSTITUTIONS', 'Has Substitutions'),
        ('INCOMPLETE', 'Incomplete'),
        ('HAS_ERRORS', 'Has Errors'),
    )

    # Link to job/work order
    job_card = models.ForeignKey(
        'production.JobCard',
        on_delete=models.CASCADE,
        related_name='cutter_maps'
    )

    # Map metadata
    map_type = models.CharField(
        max_length=20,
        choices=MAP_TYPE_CHOICES,
        help_text="Stage this map represents"
    )
    sequence_number = models.PositiveIntegerField(
        default=1,
        help_text="Sequence number for multiple reworks"
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
        help_text="All cells filled"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    completed_by = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_cutter_maps'
    )

    # Validation
    validation_status = models.CharField(
        max_length=20,
        choices=VALIDATION_STATUS_CHOICES,
        default='PENDING'
    )
    validation_notes = models.TextField(
        blank=True
    )
    last_validated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'inventory_cutter_map_header'
        verbose_name = 'Cutter Map Header'
        verbose_name_plural = 'Cutter Map Headers'
        unique_together = [
            ('job_card', 'map_type', 'sequence_number')
        ]
        indexes = [
            models.Index(fields=['job_card', 'map_type']),
            models.Index(fields=['source_bom_grid']),
            models.Index(fields=['validation_status']),
        ]
        ordering = ['job_card', 'map_type', 'sequence_number']

    def __str__(self):
        return f"{self.get_map_type_display()} - {self.job_card} (#{self.sequence_number})"

    def create_from_bom(self):
        """
        Create map cells from source BOM grid.

        This is called when initializing a new map stage.
        """
        # Delete existing cells
        self.cells.all().delete()

        # Create cells from BOM
        map_cells = []
        for bom_cell in self.source_bom_grid.cells.all():
            map_cells.append(
                CutterMapCell(
                    map_header=self,
                    blade_number=bom_cell.blade_number,
                    pocket_number=bom_cell.pocket_number,
                    is_primary=bom_cell.is_primary,
                    location_name=bom_cell.location_name,
                    section=bom_cell.section,
                    required_cutter_type=bom_cell.cutter_type,
                    cutter_sequence=bom_cell.cutter_sequence,
                    formation_order=bom_cell.formation_order,
                    status='EMPTY'
                )
            )

        # Bulk create
        if map_cells:
            CutterMapCell.objects.bulk_create(map_cells)

        return map_cells

    def validate_against_bom(self):
        """
        Validate this map against source BOM.

        Returns dict with validation results.
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'summary': {}
        }

        # Check each BOM summary
        for summary in self.source_bom_grid.summaries.all():
            cutter_type = summary.cutter_type
            required = summary.required_quantity

            # Count actual in map
            actual = self.cells.filter(
                actual_cutter_type=cutter_type
            ).count()

            remaining = required - actual

            validation_result['summary'][cutter_type.id] = {
                'cutter_type': str(cutter_type),
                'required': required,
                'actual': actual,
                'remaining': remaining,
                'status': 'OK' if remaining == 0 else ('UNDER' if remaining > 0 else 'OVER')
            }

            if remaining > 0:
                validation_result['warnings'].append(
                    f"{cutter_type}: Need {remaining} more (has {actual}/{required})"
                )
            elif remaining < 0:
                validation_result['errors'].append(
                    f"{cutter_type}: Over-entered by {abs(remaining)} (has {actual}/{required})"
                )
                validation_result['is_valid'] = False

        # Check for empty required cells
        empty_required = self.cells.filter(
            required_cutter_type__isnull=False,
            actual_cutter_type__isnull=True
        ).count()

        if empty_required > 0:
            validation_result['warnings'].append(
                f"{empty_required} required cells are still empty"
            )

        # Update validation status
        if not validation_result['is_valid']:
            self.validation_status = 'HAS_ERRORS'
        elif validation_result['warnings']:
            if any('substitut' in w.lower() for w in validation_result['warnings']):
                self.validation_status = 'HAS_SUBSTITUTIONS'
            else:
                self.validation_status = 'INCOMPLETE'
        else:
            self.validation_status = 'VALID'

        self.validation_notes = '\n'.join(
            validation_result['errors'] + validation_result['warnings']
        )
        self.last_validated_at = timezone.now()
        self.save(update_fields=['validation_status', 'validation_notes', 'last_validated_at'])

        return validation_result

    def get_color_scheme(self):
        """
        Get color scheme for this map type.

        Returns dict of status -> color mappings.
        """
        color_schemes = {
            'DESIGN': {
                'EMPTY': '#f5f5f5',
                'CORRECT': '#e3f2fd',
                'PRIMARY': '#1976d2',
                'SECONDARY': '#90caf9',
                'CRITICAL': '#ffebee',
            },
            'AS_RECEIVED': {
                'EMPTY': '#f8f9fa',
                'CORRECT': '#d4edda',
                'SUBSTITUTED': '#fff3cd',
                'DAMAGED': '#f8d7da',
                'MISSING': '#e2e3e5',
            },
            'AS_BUILT': {
                'EMPTY': '#f8f9fa',
                'CORRECT': '#d4edda',
                'SUBSTITUTED': '#ffe0b2',
                'PENDING': '#fff3cd',
                'ISSUE': '#f8d7da',
            },
            'POST_EVAL': {
                'EMPTY': '#f8f9fa',
                'CORRECT': '#d4edda',
                'MINOR_WEAR': '#fff3cd',
                'DAMAGED': '#f8d7da',
                'NEEDS_REWORK': '#ffe0b2',
            },
            'POST_NDT': {
                'EMPTY': '#f8f9fa',
                'PASS': '#d4edda',
                'REVIEW': '#fff3cd',
                'FAIL': '#f8d7da',
            },
            'POST_REWORK': {
                'EMPTY': '#f8f9fa',
                'REWORKED': '#d1ecf1',
                'REPLACED': '#cfe2ff',
                'ISSUE': '#f8d7da',
            },
            'FINAL': {
                'EMPTY': '#f8f9fa',
                'APPROVED': '#d4edda',
                'CONDITIONAL': '#fff3cd',
                'REJECTED': '#f8d7da',
            },
        }

        return color_schemes.get(self.map_type, color_schemes['DESIGN'])


class CutterMapCell(AuditMixin):
    """
    Individual cell in cutter map - tracks required vs actual.

    Each cell shows:
    - What should be there (from BOM)
    - What actually is there (as-built)
    - Status and notes from different teams
    """

    STATUS_CHOICES = (
        ('EMPTY', 'Empty'),
        ('CORRECT', 'Correct (matches BOM)'),
        ('SUBSTITUTED', 'Substituted (different type)'),
        ('DAMAGED', 'Damaged'),
        ('REWORKED', 'Reworked'),
        ('REPLACED', 'Replaced'),
        ('PENDING', 'Pending'),
    )

    map_header = models.ForeignKey(
        CutterMapHeader,
        on_delete=models.CASCADE,
        related_name='cells'
    )

    # Position (copied from BOM)
    blade_number = models.PositiveIntegerField()
    pocket_number = models.PositiveIntegerField()
    is_primary = models.BooleanField(default=True)
    location_name = models.CharField(max_length=50, blank=True)
    section = models.ForeignKey(
        'evaluation.BitSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Sequencing (copied from BOM)
    cutter_sequence = models.PositiveIntegerField(null=True, blank=True)
    formation_order = models.PositiveIntegerField(null=True, blank=True)

    # Required (from BOM)
    required_cutter_type = models.ForeignKey(
        'CutterDetail',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='map_cells_required',
        help_text="What should be installed (from BOM)"
    )

    # Actual (as-built)
    actual_cutter_type = models.ForeignKey(
        'CutterDetail',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='map_cells_actual',
        help_text="What is actually installed"
    )
    actual_cutter_serial = models.ForeignKey(
        'SerialUnit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='map_cells',
        help_text="Specific serial number installed"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='EMPTY'
    )

    # Multi-stage remarks (different teams add notes)
    technical_notes = models.TextField(
        blank=True,
        help_text="Technical/design notes"
    )
    receiving_notes = models.TextField(
        blank=True,
        help_text="Receiving inspector notes"
    )
    production_notes = models.TextField(
        blank=True,
        help_text="Production team notes"
    )
    qc_notes = models.TextField(
        blank=True,
        help_text="QC evaluation notes"
    )
    ndt_notes = models.TextField(
        blank=True,
        help_text="NDT inspection notes"
    )
    rework_notes = models.TextField(
        blank=True,
        help_text="Rework notes"
    )
    final_inspection_notes = models.TextField(
        blank=True,
        help_text="Final inspector notes"
    )

    class Meta:
        db_table = 'inventory_cutter_map_cell'
        verbose_name = 'Cutter Map Cell'
        verbose_name_plural = 'Cutter Map Cells'
        unique_together = [
            ('map_header', 'blade_number', 'pocket_number', 'is_primary')
        ]
        indexes = [
            models.Index(fields=['map_header', 'blade_number']),
            models.Index(fields=['map_header', 'status']),
            models.Index(fields=['actual_cutter_type']),
            models.Index(fields=['actual_cutter_serial']),
        ]
        ordering = ['blade_number', '-is_primary', 'pocket_number']

    def __str__(self):
        return f"{self.cell_reference}: {self.actual_cutter_type or 'Empty'}"

    @property
    def cell_reference(self):
        """Excel-like cell reference."""
        p_or_s = "P" if self.is_primary else "S"
        return f"B{self.blade_number}P{self.pocket_number}{p_or_s}"

    @property
    def color_code(self):
        """Get color code for UI rendering based on map type and status."""
        color_scheme = self.map_header.get_color_scheme()
        return color_scheme.get(self.status, '#ffffff')

    @property
    def is_match(self):
        """Check if actual matches required."""
        if not self.required_cutter_type or not self.actual_cutter_type:
            return False
        return self.required_cutter_type == self.actual_cutter_type

    def set_actual_cutter(self, cutter_type, serial_unit=None, notes=''):
        """
        Set actual cutter with validation.

        Returns (success: bool, message: str, remaining: int)
        """
        # Get BOM summary for this cutter type
        summary = self.map_header.source_bom_grid.summaries.filter(
            cutter_type=cutter_type
        ).first()

        if not summary:
            return False, f"Cutter type {cutter_type} is not in the BOM", 0

        # Check if we're over the limit (excluding this cell if already has this type)
        current_count = self.map_header.cells.filter(
            actual_cutter_type=cutter_type
        ).exclude(id=self.id).count()

        if current_count >= summary.required_quantity:
            return False, f"BOM limit reached: Already have {current_count}/{summary.required_quantity} of {cutter_type}", 0

        # Set the cutter
        self.actual_cutter_type = cutter_type
        self.actual_cutter_serial = serial_unit

        # Update status
        if self.is_match:
            self.status = 'CORRECT'
        else:
            self.status = 'SUBSTITUTED'

        self.save()

        # Calculate remaining
        new_count = current_count + 1
        remaining = summary.required_quantity - new_count

        return True, f"OK: {new_count}/{summary.required_quantity} used, {remaining} remaining", remaining

    def get_availability(self):
        """Get availability for required cutter type."""
        if not self.required_cutter_type:
            return None

        # Use grid's availability settings
        from floor_app.operations.inventory.models import CutterInventorySummary

        summary = CutterInventorySummary.objects.filter(
            cutter_detail=self.required_cutter_type
        ).first()

        if not summary:
            return None

        # Respect show_reclaimed_cutters setting
        show_reclaimed = self.map_header.source_bom_grid.show_reclaimed_cutters

        if show_reclaimed:
            total_available = summary.quantity_new_good + summary.quantity_reclaimed_good
        else:
            total_available = summary.quantity_new_good

        return {
            'cutter_type': self.required_cutter_type,
            'available_new': summary.quantity_new_good,
            'available_reclaimed': summary.quantity_reclaimed_good,
            'total_available': total_available,
            'in_transit': summary.quantity_in_transit,
            'reserved': summary.quantity_reserved,
            'show_reclaimed': show_reclaimed,
        }


class BOMUsageTracking(models.Model):
    """
    Track which bits/jobs use which BOM version.

    This provides full traceability of BOM usage and modifications.
    """

    bom_header = models.ForeignKey(
        'engineering.BOMHeader',
        on_delete=models.PROTECT,
        related_name='usage_records'
    )
    job_card = models.ForeignKey(
        'production.JobCard',
        on_delete=models.CASCADE,
        related_name='bom_usage'
    )

    # Usage details
    used_at = models.DateTimeField(
        auto_now_add=True
    )
    used_by = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bom_usage_records'
    )

    # Modification tracking
    was_modified = models.BooleanField(
        default=False,
        help_text="Was BOM modified for this job (e.g., shortage handling, testing)"
    )
    modification_notes = models.TextField(
        blank=True,
        help_text="Why BOM was modified"
    )
    modified_cells = models.JSONField(
        null=True,
        blank=True,
        help_text="Record of which cells were modified"
    )

    class Meta:
        db_table = 'inventory_bom_usage_tracking'
        verbose_name = 'BOM Usage Record'
        verbose_name_plural = 'BOM Usage Records'
        indexes = [
            models.Index(fields=['bom_header', 'used_at']),
            models.Index(fields=['job_card']),
        ]
        ordering = ['-used_at']

    def __str__(self):
        modified = " (Modified)" if self.was_modified else ""
        return f"{self.bom_header} used by {self.job_card}{modified}"
