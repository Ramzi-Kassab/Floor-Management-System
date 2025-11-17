"""
Planning & KPI - Resource Management Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from ..models import ResourceType, ResourceCapacity


@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'category', 'department', 'default_capacity_per_shift',
        'efficiency_factor', 'is_bottleneck', 'is_active'
    ]
    list_filter = ['category', 'is_bottleneck', 'is_active', 'department']
    search_fields = ['code', 'name', 'description', 'department']
    ordering = ['category', 'code']
    readonly_fields = ['public_id', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        ('Resource Identification', {
            'fields': ('code', 'name', 'description', 'category', 'department')
        }),
        ('Capacity Settings', {
            'fields': (
                'default_capacity_per_shift', 'efficiency_factor',
                'setup_time_minutes', 'min_batch_size'
            )
        }),
        ('Planning Flags', {
            'fields': ('is_bottleneck', 'is_active')
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )


@admin.register(ResourceCapacity)
class ResourceCapacityAdmin(admin.ModelAdmin):
    list_display = [
        'resource_type', 'date', 'shift', 'available_hours', 'reserved_hours',
        'planned_load_hours', 'utilization_display', 'is_overloaded_display'
    ]
    list_filter = ['resource_type', 'shift', 'date']
    search_fields = ['resource_type__code', 'resource_type__name', 'notes']
    date_hierarchy = 'date'
    ordering = ['date', 'resource_type']
    readonly_fields = [
        'public_id', 'utilization_display', 'is_overloaded_display',
        'remaining_capacity_display',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    fieldsets = (
        ('Resource & Date', {
            'fields': ('resource_type', 'date', 'shift')
        }),
        ('Capacity', {
            'fields': ('available_hours', 'reserved_hours')
        }),
        ('Load', {
            'fields': ('planned_load_hours', 'actual_load_hours')
        }),
        ('Calculated Metrics', {
            'fields': (
                'utilization_display', 'is_overloaded_display',
                'remaining_capacity_display'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def utilization_display(self, obj):
        pct = obj.utilization_percentage
        if pct > 100:
            return format_html(
                '<span style="color: red; font-weight: bold;">{:.1f}% OVERLOADED</span>',
                pct
            )
        if pct > 85:
            return format_html(
                '<span style="color: orange;">{:.1f}%</span>',
                pct
            )
        return f'{pct:.1f}%'

    utilization_display.short_description = 'Utilization'

    def is_overloaded_display(self, obj):
        if obj.is_overloaded:
            return format_html('<span style="color: red;">✗ Overloaded</span>')
        return format_html('<span style="color: green;">✓ OK</span>')

    is_overloaded_display.short_description = 'Status'

    def remaining_capacity_display(self, obj):
        remaining = obj.remaining_capacity
        if remaining < 0:
            return format_html(
                '<span style="color: red;">{:.2f} hrs (Deficit)</span>',
                remaining
            )
        return f'{remaining:.2f} hrs'

    remaining_capacity_display.short_description = 'Remaining Capacity'
