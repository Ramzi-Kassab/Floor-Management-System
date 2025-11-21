"""
Bit Design Admin

Admin interface for managing bit designs and revisions (MAT numbers).

MOVED FROM: floor_app.operations.inventory.admin (portions)
REASON: Engineering owns design definitions, not inventory
"""

from django.contrib import admin
from floor_app.operations.engineering.models import (
    BitDesignLevel, BitDesignType, BitDesign, BitDesignRevision
)


@admin.register(BitDesignLevel)
class BitDesignLevelAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    ordering = ['sort_order', 'code']
    fields = ['code', 'name', 'description', 'sort_order', 'is_active']


@admin.register(BitDesignType)
class BitDesignTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    ordering = ['sort_order', 'code']
    fields = ['code', 'name', 'description', 'sort_order', 'is_active']


class BitDesignRevisionInline(admin.TabularInline):
    model = BitDesignRevision
    extra = 0
    fields = [
        'mat_number', 'revision_code', 'design_type',
        'is_temporary', 'is_active', 'effective_date'
    ]
    raw_id_fields = ['design_type', 'superseded_by']


@admin.register(BitDesign)
class BitDesignAdmin(admin.ModelAdmin):
    list_display = [
        'design_code', 'name', 'level', 'bit_category',
        'size_inches', 'blade_count', 'is_active', 'created_at'
    ]
    list_filter = ['bit_category', 'level', 'is_active', 'is_deleted']
    search_fields = ['design_code', 'name']
    ordering = ['-created_at']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    raw_id_fields = ['level']
    inlines = [BitDesignRevisionInline]

    fieldsets = (
        ('Identification', {
            'fields': ('design_code', 'name', 'public_id', 'bit_category')
        }),
        ('Design Level', {
            'fields': ('level',)
        }),
        ('Specifications', {
            'fields': (
                'size_inches', 'connection_type', 'blade_count',
                'total_cutter_count', 'nozzle_count', 'tfa_range'
            )
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('level')


@admin.register(BitDesignRevision)
class BitDesignRevisionAdmin(admin.ModelAdmin):
    list_display = [
        'mat_number', 'bit_design', 'revision_code', 'design_type',
        'is_temporary', 'is_active', 'effective_date', 'created_at'
    ]
    list_filter = ['is_temporary', 'is_active', 'design_type', 'is_deleted']
    search_fields = ['mat_number', 'bit_design__design_code']
    ordering = ['-created_at']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    raw_id_fields = ['bit_design', 'design_type', 'superseded_by']

    fieldsets = (
        ('Identification', {
            'fields': ('mat_number', 'bit_design', 'revision_code', 'public_id')
        }),
        ('Type', {
            'fields': ('design_type',)
        }),
        ('Status', {
            'fields': ('is_temporary', 'is_active', 'superseded_by')
        }),
        ('Dates', {
            'fields': ('effective_date', 'obsolete_date')
        }),
        ('Change History', {
            'fields': ('change_reason', 'notes')
        }),
        ('ERP Integration', {
            'fields': ('erp_item_number', 'erp_bom_number', 'standard_cost', 'last_purchase_cost'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bit_design', 'design_type')
