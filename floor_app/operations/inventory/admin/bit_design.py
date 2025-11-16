from django.contrib import admin
from floor_app.operations.inventory.models import (
    BitDesignLevel,
    BitDesignType,
    BitDesign,
    BitDesignRevision,
)


@admin.register(BitDesignLevel)
class BitDesignLevelAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    ordering = ['sort_order', 'code']


@admin.register(BitDesignType)
class BitDesignTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    ordering = ['sort_order', 'code']


class BitDesignRevisionInline(admin.TabularInline):
    model = BitDesignRevision
    extra = 0
    fields = ['mat_number', 'revision_code', 'design_type', 'is_temporary', 'is_active', 'effective_date']
    readonly_fields = ['created_at']
    show_change_link = True


@admin.register(BitDesign)
class BitDesignAdmin(admin.ModelAdmin):
    list_display = [
        'design_code', 'name', 'level', 'size_inches',
        'connection_type', 'blade_count', 'created_at'
    ]
    list_filter = ['level', 'is_deleted']
    search_fields = ['design_code', 'name', 'connection_type']
    ordering = ['-created_at']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [BitDesignRevisionInline]

    fieldsets = (
        ('Identification', {
            'fields': ('design_code', 'name', 'public_id', 'level')
        }),
        ('Design Specifications', {
            'fields': ('size_inches', 'connection_type', 'blade_count', 'total_cutter_count',
                      'nozzle_count', 'tfa_range')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BitDesignRevision)
class BitDesignRevisionAdmin(admin.ModelAdmin):
    list_display = [
        'mat_number', 'bit_design', 'revision_code', 'design_type',
        'is_temporary', 'is_active', 'effective_date'
    ]
    list_filter = ['is_active', 'is_temporary', 'design_type', 'bit_design__level']
    search_fields = ['mat_number', 'bit_design__design_code']
    ordering = ['-created_at']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    raw_id_fields = ['bit_design', 'superseded_by']

    fieldsets = (
        ('MAT Identification', {
            'fields': ('mat_number', 'bit_design', 'revision_code', 'design_type', 'public_id')
        }),
        ('Status', {
            'fields': ('is_temporary', 'is_active', 'effective_date', 'obsolete_date', 'superseded_by')
        }),
        ('Change Information', {
            'fields': ('change_reason', 'notes')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bit_design', 'design_type')
