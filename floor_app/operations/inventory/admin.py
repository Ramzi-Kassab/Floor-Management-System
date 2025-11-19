"""
Django Admin for Inventory Models

Admin interface for managing cutter BOM grids and maps.
"""

from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from floor_app.operations.inventory.models import (
    CutterBOMGridHeader,
    CutterBOMGridCell,
    CutterBOMSummary,
    CutterMapHeader,
    CutterMapCell,
    BOMUsageTracking,
)


class CutterBOMGridCellInline(admin.TabularInline):
    """Inline editor for BOM grid cells."""

    model = CutterBOMGridCell
    extra = 0
    fields = (
        'blade_number',
        'pocket_number',
        'is_primary',
        'location_name',
        'section',
        'cutter_type',
        'cutter_sequence',
        'formation_order',
    )
    readonly_fields = ('cutter_sequence',)
    autocomplete_fields = ['cutter_type', 'section']

    def get_queryset(self, request):
        """Optimize queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('cutter_type', 'section')


class CutterBOMSummaryInline(admin.TabularInline):
    """Inline display of BOM summary (read-only)."""

    model = CutterBOMSummary
    extra = 0
    fields = (
        'cutter_type',
        'required_quantity',
        'primary_count',
        'secondary_count',
        'last_calculated',
    )
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CutterBOMGridHeader)
class CutterBOMGridHeaderAdmin(admin.ModelAdmin):
    """Admin for Cutter BOM Grid Headers."""

    list_display = (
        'bom_header',
        'blade_count',
        'max_pockets_per_blade',
        'cutter_ordering_scheme',
        'total_primary_cutters',
        'total_secondary_cutters',
        'show_reclaimed_cutters',
        'created_at',
    )
    list_filter = (
        'cutter_ordering_scheme',
        'show_reclaimed_cutters',
        'created_at',
    )
    search_fields = (
        'bom_header__bom_number',
        'bom_header__name',
    )
    readonly_fields = (
        'total_primary_cutters',
        'total_secondary_cutters',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        ('BOM Reference', {
            'fields': ('bom_header',)
        }),
        ('Grid Configuration', {
            'fields': (
                'blade_count',
                'max_pockets_per_blade',
                'cutter_ordering_scheme',
            )
        }),
        ('Display Options', {
            'fields': ('show_reclaimed_cutters',)
        }),
        ('Summary (Auto-calculated)', {
            'fields': (
                'total_primary_cutters',
                'total_secondary_cutters',
            ),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [CutterBOMGridCellInline, CutterBOMSummaryInline]

    actions = ['recalculate_totals', 'refresh_summaries', 'assign_sequences']

    def recalculate_totals(self, request, queryset):
        """Recalculate total primary and secondary counts."""
        count = 0
        for grid in queryset:
            grid.recalculate_totals()
            count += 1
        self.message_user(request, f"Recalculated totals for {count} grid(s)")

    recalculate_totals.short_description = "Recalculate totals"

    def refresh_summaries(self, request, queryset):
        """Refresh BOM summaries."""
        count = 0
        for grid in queryset:
            grid.refresh_summaries()
            count += 1
        self.message_user(request, f"Refreshed summaries for {count} grid(s)")

    refresh_summaries.short_description = "Refresh BOM summaries"

    def assign_sequences(self, request, queryset):
        """Assign sequence numbers to all cells."""
        count = 0
        for grid in queryset:
            grid.assign_all_sequence_numbers()
            count += 1
        self.message_user(request, f"Assigned sequences for {count} grid(s)")

    assign_sequences.short_description = "Assign sequence numbers"


@admin.register(CutterBOMGridCell)
class CutterBOMGridCellAdmin(admin.ModelAdmin):
    """Admin for individual BOM grid cells."""

    list_display = (
        'cell_reference',
        'grid_header',
        'blade_number',
        'pocket_number',
        'is_primary',
        'location_name',
        'cutter_type',
        'cutter_sequence',
    )
    list_filter = (
        'grid_header',
        'is_primary',
        'blade_number',
        'section',
    )
    search_fields = (
        'grid_header__bom_header__bom_number',
        'location_name',
        'cutter_type__cutter_code',
    )
    readonly_fields = ('cell_reference', 'created_at', 'updated_at')
    autocomplete_fields = ['grid_header', 'cutter_type', 'section']

    fieldsets = (
        ('Position', {
            'fields': (
                'grid_header',
                'blade_number',
                'pocket_number',
                'is_primary',
                'cell_reference',
            )
        }),
        ('Location', {
            'fields': ('location_name', 'section')
        }),
        ('Cutter Specification', {
            'fields': (
                'cutter_type',
                'cutter_sequence',
                'formation_order',
            )
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class CutterMapCellInline(admin.TabularInline):
    """Inline editor for map cells."""

    model = CutterMapCell
    extra = 0
    fields = (
        'cell_reference',
        'blade_number',
        'pocket_number',
        'is_primary',
        'required_cutter_type',
        'actual_cutter_type',
        'actual_cutter_serial',
        'status',
        'color_display',
    )
    readonly_fields = ('cell_reference', 'color_display')
    autocomplete_fields = ['actual_cutter_type', 'actual_cutter_serial']

    def color_display(self, obj):
        """Display color code."""
        if obj.id:
            return format_html(
                '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px;">{}</span>',
                obj.color_code,
                obj.status
            )
        return "-"

    color_display.short_description = "Color"

    def get_queryset(self, request):
        """Optimize queryset."""
        qs = super().get_queryset(request)
        return qs.select_related(
            'required_cutter_type',
            'actual_cutter_type',
            'actual_cutter_serial'
        )


@admin.register(CutterMapHeader)
class CutterMapHeaderAdmin(admin.ModelAdmin):
    """Admin for Cutter Map Headers."""

    list_display = (
        '__str__',
        'job_card',
        'map_type',
        'sequence_number',
        'validation_status_display',
        'is_complete',
        'completed_at',
    )
    list_filter = (
        'map_type',
        'validation_status',
        'is_complete',
        'created_at',
    )
    search_fields = (
        'job_card__job_card_number',
        'source_bom_grid__bom_header__bom_number',
    )
    readonly_fields = (
        'validation_status',
        'last_validated_at',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = ['job_card', 'source_bom_grid', 'completed_by']

    fieldsets = (
        ('Job Reference', {
            'fields': ('job_card', 'map_type', 'sequence_number')
        }),
        ('Source BOM', {
            'fields': ('source_bom_grid',)
        }),
        ('Completion', {
            'fields': (
                'is_complete',
                'completed_at',
                'completed_by',
            )
        }),
        ('Validation', {
            'fields': (
                'validation_status',
                'validation_notes',
                'last_validated_at',
            ),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [CutterMapCellInline]

    actions = ['create_from_bom', 'validate_maps', 'mark_complete']

    def validation_status_display(self, obj):
        """Display validation status with color."""
        colors = {
            'PENDING': 'gray',
            'VALID': 'green',
            'HAS_SUBSTITUTIONS': 'orange',
            'INCOMPLETE': 'blue',
            'HAS_ERRORS': 'red',
        }
        color = colors.get(obj.validation_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_validation_status_display()
        )

    validation_status_display.short_description = "Validation"

    def create_from_bom(self, request, queryset):
        """Create/recreate map cells from source BOM."""
        count = 0
        for map_header in queryset:
            map_header.create_from_bom()
            count += 1
        self.message_user(request, f"Created cells for {count} map(s)")

    create_from_bom.short_description = "Create cells from BOM"

    def validate_maps(self, request, queryset):
        """Validate maps against BOM."""
        results = []
        for map_header in queryset:
            validation = map_header.validate_against_bom()
            results.append(f"{map_header}: {validation['summary']}")

        self.message_user(request, f"Validated {len(results)} map(s)")

    validate_maps.short_description = "Validate against BOM"

    def mark_complete(self, request, queryset):
        """Mark maps as complete."""
        from django.utils import timezone

        count = queryset.update(
            is_complete=True,
            completed_at=timezone.now()
        )
        self.message_user(request, f"Marked {count} map(s) as complete")

    mark_complete.short_description = "Mark as complete"


@admin.register(CutterMapCell)
class CutterMapCellAdmin(admin.ModelAdmin):
    """Admin for individual map cells."""

    list_display = (
        'cell_reference',
        'map_header',
        'blade_number',
        'pocket_number',
        'is_primary',
        'required_cutter_type',
        'actual_cutter_type',
        'status_display',
        'is_match',
    )
    list_filter = (
        'map_header__map_type',
        'status',
        'is_primary',
        'blade_number',
    )
    search_fields = (
        'map_header__job_card__job_card_number',
        'location_name',
        'actual_cutter_type__cutter_code',
    )
    readonly_fields = (
        'cell_reference',
        'is_match',
        'color_code',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = [
        'map_header',
        'required_cutter_type',
        'actual_cutter_type',
        'actual_cutter_serial',
        'section',
    ]

    fieldsets = (
        ('Map Reference', {
            'fields': ('map_header', 'cell_reference')
        }),
        ('Position', {
            'fields': (
                'blade_number',
                'pocket_number',
                'is_primary',
                'location_name',
                'section',
            )
        }),
        ('Sequencing', {
            'fields': ('cutter_sequence', 'formation_order')
        }),
        ('Cutter Specification', {
            'fields': (
                'required_cutter_type',
                'actual_cutter_type',
                'actual_cutter_serial',
                'is_match',
            )
        }),
        ('Status', {
            'fields': ('status', 'color_code')
        }),
        ('Technical Notes', {
            'fields': ('technical_notes',),
            'classes': ('collapse',)
        }),
        ('Receiving Notes', {
            'fields': ('receiving_notes',),
            'classes': ('collapse',)
        }),
        ('Production Notes', {
            'fields': ('production_notes',),
            'classes': ('collapse',)
        }),
        ('QC Notes', {
            'fields': ('qc_notes',),
            'classes': ('collapse',)
        }),
        ('NDT Notes', {
            'fields': ('ndt_notes',),
            'classes': ('collapse',)
        }),
        ('Rework Notes', {
            'fields': ('rework_notes',),
            'classes': ('collapse',)
        }),
        ('Final Inspection Notes', {
            'fields': ('final_inspection_notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):
        """Display status with color."""
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px;">{}</span>',
            obj.color_code,
            obj.get_status_display()
        )

    status_display.short_description = "Status"


@admin.register(BOMUsageTracking)
class BOMUsageTrackingAdmin(admin.ModelAdmin):
    """Admin for BOM usage tracking."""

    list_display = (
        'bom_header',
        'job_card',
        'used_at',
        'used_by',
        'was_modified',
    )
    list_filter = (
        'was_modified',
        'used_at',
    )
    search_fields = (
        'bom_header__bom_number',
        'job_card__job_card_number',
        'used_by__employee_number',
    )
    readonly_fields = ('used_at',)
    autocomplete_fields = ['bom_header', 'job_card', 'used_by']

    fieldsets = (
        ('Usage', {
            'fields': ('bom_header', 'job_card', 'used_at', 'used_by')
        }),
        ('Modifications', {
            'fields': (
                'was_modified',
                'modification_notes',
                'modified_cells',
            )
        }),
    )

    def has_add_permission(self, request):
        """Usage records are auto-created."""
        return False
