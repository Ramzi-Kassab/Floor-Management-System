from django.contrib import admin
from floor_app.operations.inventory.models import BOMHeader, BOMLine


class BOMLineInline(admin.TabularInline):
    model = BOMLine
    extra = 1
    fields = [
        'line_number', 'component_item', 'quantity_required', 'uom',
        'is_optional', 'scrap_factor', 'unit_cost'
    ]
    raw_id_fields = ['component_item', 'uom']


@admin.register(BOMHeader)
class BOMHeaderAdmin(admin.ModelAdmin):
    list_display = [
        'bom_number', 'name', 'bom_type', 'target_mat',
        'revision', 'status', 'is_active', 'created_at'
    ]
    list_filter = ['bom_type', 'status', 'is_active', 'is_deleted']
    search_fields = ['bom_number', 'name', 'target_mat__mat_number']
    ordering = ['-created_at']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    raw_id_fields = ['target_mat', 'source_mat', 'superseded_by']
    inlines = [BOMLineInline]

    fieldsets = (
        ('Identification', {
            'fields': ('bom_number', 'name', 'public_id', 'description')
        }),
        ('Type and Target', {
            'fields': ('bom_type', 'target_mat', 'source_mat')
        }),
        ('Version Control', {
            'fields': ('revision', 'status', 'is_active', 'superseded_by')
        }),
        ('Effectivity', {
            'fields': ('effective_date', 'obsolete_date')
        }),
        ('Estimates', {
            'fields': ('estimated_labor_hours', 'estimated_material_cost')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('target_mat', 'source_mat')


@admin.register(BOMLine)
class BOMLineAdmin(admin.ModelAdmin):
    list_display = [
        'bom_header', 'line_number', 'component_item',
        'quantity_required', 'uom', 'is_optional', 'scrap_factor'
    ]
    list_filter = ['is_optional', 'bom_header__bom_type']
    search_fields = ['bom_header__bom_number', 'component_item__sku']
    ordering = ['bom_header', 'line_number']
    raw_id_fields = ['bom_header', 'component_item', 'uom', 'required_condition', 'required_ownership']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'bom_header', 'component_item', 'uom'
        )
