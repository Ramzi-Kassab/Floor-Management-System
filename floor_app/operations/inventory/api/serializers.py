"""
Cutter BOM & Map Grid System API Serializers

Serializers for Cutter BOM and Map grid system REST API.
"""

from rest_framework import serializers
from floor_app.operations.inventory.models import (
    CutterBOMGrid,
    CutterBOMGridRow,
    CutterBOMGridColumn,
    CutterBOMGridCell,
    CutterBOMGridValidation,
    CutterBOMGridHistory,
    CutterMapGrid,
    CutterMapGridRow,
    CutterMapGridColumn,
    CutterMapGridCell,
    CutterMapGridValidation,
    CutterMapGridHistory
)


# ==================== Cutter BOM Grid Serializers ====================

class CutterBOMGridColumnSerializer(serializers.ModelSerializer):
    """Serializer for BOM grid columns."""

    data_type_display = serializers.CharField(
        source='get_data_type_display',
        read_only=True
    )

    class Meta:
        model = CutterBOMGridColumn
        fields = [
            'id',
            'grid',
            'column_index',
            'column_name',
            'column_key',
            'data_type',
            'data_type_display',
            'is_required',
            'is_readonly',
            'default_value',
            'validation_rules',
            'width_pixels',
            'is_visible',
            'display_order',
            'help_text',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class CutterBOMGridRowSerializer(serializers.ModelSerializer):
    """Serializer for BOM grid rows."""

    class Meta:
        model = CutterBOMGridRow
        fields = [
            'id',
            'grid',
            'row_index',
            'row_label',
            'is_header',
            'is_locked',
            'is_visible',
            'display_order',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class CutterBOMGridCellSerializer(serializers.ModelSerializer):
    """Serializer for BOM grid cells."""

    column_name = serializers.CharField(source='column.column_name', read_only=True)
    row_label = serializers.CharField(source='row.row_label', read_only=True)
    validation_status_display = serializers.CharField(
        source='get_validation_status_display',
        read_only=True
    )
    edited_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CutterBOMGridCell
        fields = [
            'id',
            'grid',
            'row',
            'row_label',
            'column',
            'column_name',
            'cell_value',
            'previous_value',
            'validation_status',
            'validation_status_display',
            'validation_errors',
            'is_modified',
            'is_locked',
            'edited_by',
            'edited_by_name',
            'edited_at',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['previous_value', 'edited_at', 'created_at']

    def get_edited_by_name(self, obj):
        """Get editor's name."""
        if obj.edited_by:
            return obj.edited_by.get_full_name() or obj.edited_by.username
        return None


class CutterBOMGridCellUpdateSerializer(serializers.Serializer):
    """Serializer for updating a cell value."""

    cell_value = serializers.CharField(allow_blank=True)
    validate_on_save = serializers.BooleanField(default=True)


class CutterBOMGridCellBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating cells."""

    updates = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of cell updates [{row_id, column_id, value}, ...]"
    )
    validate_on_save = serializers.BooleanField(default=True)


class CutterBOMGridValidationSerializer(serializers.ModelSerializer):
    """Serializer for BOM grid validation rules."""

    validation_type_display = serializers.CharField(
        source='get_validation_type_display',
        read_only=True
    )

    class Meta:
        model = CutterBOMGridValidation
        fields = [
            'id',
            'grid',
            'validation_name',
            'validation_type',
            'validation_type_display',
            'validation_rule',
            'error_message',
            'is_active',
            'applies_to_columns',
            'applies_to_rows',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['created_at']


class CutterBOMGridHistorySerializer(serializers.ModelSerializer):
    """Serializer for BOM grid history."""

    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CutterBOMGridHistory
        fields = [
            'id',
            'grid',
            'action',
            'action_display',
            'changed_by',
            'changed_by_name',
            'changed_at',
            'cell_reference',
            'old_value',
            'new_value',
            'metadata',
        ]
        read_only_fields = ['changed_at']

    def get_changed_by_name(self, obj):
        """Get user's name who made the change."""
        if obj.changed_by:
            return obj.changed_by.get_full_name() or obj.changed_by.username
        return 'System'


class CutterBOMGridSerializer(serializers.ModelSerializer):
    """Serializer for BOM grids."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    created_by_name = serializers.SerializerMethodField()
    stage_display = serializers.CharField(
        source='get_stage_display',
        read_only=True
    )
    columns = CutterBOMGridColumnSerializer(many=True, read_only=True)
    rows = CutterBOMGridRowSerializer(many=True, read_only=True)
    total_cells = serializers.SerializerMethodField()
    modified_cells_count = serializers.SerializerMethodField()
    validation_errors_count = serializers.SerializerMethodField()

    class Meta:
        model = CutterBOMGrid
        fields = [
            'id',
            'grid_name',
            'description',
            'job_order',
            'cutter_serial',
            'stage',
            'stage_display',
            'status',
            'status_display',
            'version',
            'is_locked',
            'locked_by',
            'locked_at',
            'created_by',
            'created_by_name',
            'columns',
            'rows',
            'total_cells',
            'modified_cells_count',
            'validation_errors_count',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['version', 'locked_at', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        """Get creator's name."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'System'

    def get_total_cells(self, obj):
        """Get total number of cells."""
        return obj.cells.count()

    def get_modified_cells_count(self, obj):
        """Get count of modified cells."""
        return obj.cells.filter(is_modified=True).count()

    def get_validation_errors_count(self, obj):
        """Get count of cells with validation errors."""
        return obj.cells.filter(validation_status='ERROR').count()


class CutterBOMGridCreateSerializer(serializers.Serializer):
    """Serializer for creating a new BOM grid."""

    grid_name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    job_order_id = serializers.IntegerField(required=False)
    cutter_serial_id = serializers.IntegerField(required=False)
    stage = serializers.ChoiceField(
        choices=['DESIGN', 'RECEIVING', 'PRODUCTION', 'QC', 'NDT', 'REWORK', 'FINAL'],
        default='DESIGN'
    )
    template_id = serializers.IntegerField(
        required=False,
        help_text="ID of template grid to copy structure from"
    )
    rows_count = serializers.IntegerField(default=50, min_value=1, max_value=1000)
    metadata = serializers.JSONField(required=False)


# ==================== Cutter Map Grid Serializers ====================

class CutterMapGridColumnSerializer(serializers.ModelSerializer):
    """Serializer for Map grid columns."""

    data_type_display = serializers.CharField(
        source='get_data_type_display',
        read_only=True
    )

    class Meta:
        model = CutterMapGridColumn
        fields = [
            'id',
            'grid',
            'column_index',
            'column_name',
            'column_key',
            'data_type',
            'data_type_display',
            'is_required',
            'is_readonly',
            'default_value',
            'validation_rules',
            'width_pixels',
            'is_visible',
            'display_order',
            'help_text',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class CutterMapGridRowSerializer(serializers.ModelSerializer):
    """Serializer for Map grid rows."""

    class Meta:
        model = CutterMapGridRow
        fields = [
            'id',
            'grid',
            'row_index',
            'row_label',
            'is_header',
            'is_locked',
            'is_visible',
            'display_order',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class CutterMapGridCellSerializer(serializers.ModelSerializer):
    """Serializer for Map grid cells."""

    column_name = serializers.CharField(source='column.column_name', read_only=True)
    row_label = serializers.CharField(source='row.row_label', read_only=True)
    validation_status_display = serializers.CharField(
        source='get_validation_status_display',
        read_only=True
    )
    edited_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CutterMapGridCell
        fields = [
            'id',
            'grid',
            'row',
            'row_label',
            'column',
            'column_name',
            'cell_value',
            'previous_value',
            'validation_status',
            'validation_status_display',
            'validation_errors',
            'is_modified',
            'is_locked',
            'edited_by',
            'edited_by_name',
            'edited_at',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['previous_value', 'edited_at', 'created_at']

    def get_edited_by_name(self, obj):
        """Get editor's name."""
        if obj.edited_by:
            return obj.edited_by.get_full_name() or obj.edited_by.username
        return None


class CutterMapGridValidationSerializer(serializers.ModelSerializer):
    """Serializer for Map grid validation rules."""

    validation_type_display = serializers.CharField(
        source='get_validation_type_display',
        read_only=True
    )

    class Meta:
        model = CutterMapGridValidation
        fields = [
            'id',
            'grid',
            'validation_name',
            'validation_type',
            'validation_type_display',
            'validation_rule',
            'error_message',
            'is_active',
            'applies_to_columns',
            'applies_to_rows',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['created_at']


class CutterMapGridHistorySerializer(serializers.ModelSerializer):
    """Serializer for Map grid history."""

    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CutterMapGridHistory
        fields = [
            'id',
            'grid',
            'action',
            'action_display',
            'changed_by',
            'changed_by_name',
            'changed_at',
            'cell_reference',
            'old_value',
            'new_value',
            'metadata',
        ]
        read_only_fields = ['changed_at']

    def get_changed_by_name(self, obj):
        """Get user's name who made the change."""
        if obj.changed_by:
            return obj.changed_by.get_full_name() or obj.changed_by.username
        return 'System'


class CutterMapGridSerializer(serializers.ModelSerializer):
    """Serializer for Map grids."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    created_by_name = serializers.SerializerMethodField()
    stage_display = serializers.CharField(
        source='get_stage_display',
        read_only=True
    )
    columns = CutterMapGridColumnSerializer(many=True, read_only=True)
    rows = CutterMapGridRowSerializer(many=True, read_only=True)
    total_cells = serializers.SerializerMethodField()
    modified_cells_count = serializers.SerializerMethodField()
    validation_errors_count = serializers.SerializerMethodField()

    class Meta:
        model = CutterMapGrid
        fields = [
            'id',
            'grid_name',
            'description',
            'job_order',
            'cutter_serial',
            'stage',
            'stage_display',
            'status',
            'status_display',
            'version',
            'is_locked',
            'locked_by',
            'locked_at',
            'created_by',
            'created_by_name',
            'columns',
            'rows',
            'total_cells',
            'modified_cells_count',
            'validation_errors_count',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['version', 'locked_at', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        """Get creator's name."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'System'

    def get_total_cells(self, obj):
        """Get total number of cells."""
        return obj.cells.count()

    def get_modified_cells_count(self, obj):
        """Get count of modified cells."""
        return obj.cells.filter(is_modified=True).count()

    def get_validation_errors_count(self, obj):
        """Get count of cells with validation errors."""
        return obj.cells.filter(validation_status='ERROR').count()


class CutterMapGridCreateSerializer(serializers.Serializer):
    """Serializer for creating a new Map grid."""

    grid_name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    job_order_id = serializers.IntegerField(required=False)
    cutter_serial_id = serializers.IntegerField(required=False)
    stage = serializers.ChoiceField(
        choices=['DESIGN', 'RECEIVING', 'PRODUCTION', 'QC', 'NDT', 'REWORK', 'FINAL'],
        default='DESIGN'
    )
    template_id = serializers.IntegerField(
        required=False,
        help_text="ID of template grid to copy structure from"
    )
    rows_count = serializers.IntegerField(default=50, min_value=1, max_value=1000)
    metadata = serializers.JSONField(required=False)


# ==================== Common Serializers ====================

class GridComparisonSerializer(serializers.Serializer):
    """Serializer for comparing two grids."""

    source_grid_id = serializers.IntegerField()
    target_grid_id = serializers.IntegerField()
    comparison_type = serializers.ChoiceField(
        choices=['VALUES', 'STRUCTURE', 'BOTH'],
        default='VALUES'
    )


class GridCloneSerializer(serializers.Serializer):
    """Serializer for cloning a grid."""

    new_name = serializers.CharField(max_length=200)
    include_data = serializers.BooleanField(default=True)
    include_validations = serializers.BooleanField(default=True)


class GridExportSerializer(serializers.Serializer):
    """Serializer for exporting grid to Excel."""

    format = serializers.ChoiceField(
        choices=['XLSX', 'CSV'],
        default='XLSX'
    )
    include_metadata = serializers.BooleanField(default=False)
    include_history = serializers.BooleanField(default=False)


class GridImportSerializer(serializers.Serializer):
    """Serializer for importing grid from Excel."""

    file = serializers.FileField()
    validate_on_import = serializers.BooleanField(default=True)
    skip_errors = serializers.BooleanField(default=False)
    update_existing = serializers.BooleanField(default=False)
