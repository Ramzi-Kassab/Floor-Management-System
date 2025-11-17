"""
Admin configuration for Asset models.
"""
from django.contrib import admin
from floor_app.operations.maintenance.models import (
    AssetCategory,
    AssetLocation,
    Asset,
    AssetDocument,
)


class AssetDocumentInline(admin.TabularInline):
    model = AssetDocument
    extra = 0
    fields = ['title', 'doc_type', 'file', 'version', 'is_current_version']
    readonly_fields = ['created_at', 'created_by']


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'parent', 'default_pm_interval_days',
        'requires_certification', 'sort_order', 'asset_count'
    ]
    list_filter = ['requires_certification', 'parent', 'is_deleted']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'code']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    list_editable = ['sort_order']

    fieldsets = (
        ('Identification', {
            'fields': ('code', 'name', 'description', 'public_id')
        }),
        ('Hierarchy', {
            'fields': ('parent', 'sort_order')
        }),
        ('PM Settings', {
            'fields': ('default_pm_interval_days', 'requires_certification')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def asset_count(self, obj):
        return obj.asset_count
    asset_count.short_description = 'Assets'


@admin.register(AssetLocation)
class AssetLocationAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'parent', 'building', 'floor_level',
        'responsible_person_name', 'is_active', 'asset_count'
    ]
    list_filter = ['is_active', 'parent', 'building', 'is_deleted']
    search_fields = ['code', 'name', 'description', 'building']
    ordering = ['sort_order', 'code']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    list_editable = ['is_active', 'sort_order']

    fieldsets = (
        ('Identification', {
            'fields': ('code', 'name', 'description', 'public_id')
        }),
        ('Hierarchy', {
            'fields': ('parent', 'sort_order')
        }),
        ('Physical Location', {
            'fields': ('building', 'floor_level')
        }),
        ('Contact', {
            'fields': ('responsible_person_id', 'responsible_person_name', 'contact_phone')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def asset_count(self, obj):
        return obj.asset_count
    asset_count.short_description = 'Assets'


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        'asset_code', 'name', 'category', 'location', 'status',
        'criticality', 'is_critical_production_asset', 'last_maintenance_date',
        'next_pm_due_date', 'pm_overdue'
    ]
    list_filter = [
        'status', 'criticality', 'is_critical_production_asset',
        'category', 'location', 'is_deleted'
    ]
    search_fields = [
        'asset_code', 'name', 'description', 'serial_number',
        'manufacturer', 'model_number', 'erp_asset_number'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'public_id', 'qr_token', 'created_at', 'updated_at',
        'created_by', 'updated_by', 'days_since_last_maintenance',
        'is_under_warranty', 'pm_overdue'
    ]
    raw_id_fields = ['category', 'location', 'parent_asset']
    inlines = [AssetDocumentInline]
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        ('Identification', {
            'fields': (
                'asset_code', 'name', 'description', 'public_id', 'qr_token'
            )
        }),
        ('Classification', {
            'fields': ('category', 'location', 'parent_asset')
        }),
        ('Manufacturer Info', {
            'fields': ('manufacturer', 'model_number', 'serial_number')
        }),
        ('Status & Criticality', {
            'fields': (
                'status', 'criticality', 'is_critical_production_asset'
            )
        }),
        ('Important Dates', {
            'fields': (
                'installation_date', 'warranty_expiry_date', 'is_under_warranty',
                'last_maintenance_date', 'next_pm_due_date', 'days_since_last_maintenance',
                'pm_overdue'
            )
        }),
        ('Financial', {
            'fields': (
                'purchase_date', 'purchase_cost', 'replacement_cost',
                'depreciation_rate'
            ),
            'classes': ('collapse',)
        }),
        ('ERP Integration', {
            'fields': ('erp_asset_number',),
            'classes': ('collapse',)
        }),
        ('Meter Tracking', {
            'fields': (
                'current_meter_reading', 'meter_unit', 'last_meter_update'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('specifications', 'notes'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'location')

    def pm_overdue(self, obj):
        return obj.pm_overdue
    pm_overdue.boolean = True
    pm_overdue.short_description = 'PM Overdue'


@admin.register(AssetDocument)
class AssetDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'title', 'doc_type', 'version',
        'is_current_version', 'file_extension', 'created_at'
    ]
    list_filter = ['doc_type', 'is_current_version', 'is_deleted']
    search_fields = ['title', 'description', 'asset__asset_code', 'asset__name']
    ordering = ['-created_at']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'file_extension']
    raw_id_fields = ['asset']

    fieldsets = (
        ('Document Info', {
            'fields': ('asset', 'title', 'doc_type', 'file', 'description')
        }),
        ('Version Control', {
            'fields': ('version', 'is_current_version')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset')

    def file_extension(self, obj):
        return obj.file_extension
    file_extension.short_description = 'Type'
