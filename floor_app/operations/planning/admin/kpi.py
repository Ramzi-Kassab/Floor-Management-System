"""
Planning & KPI - KPI Definition and Value Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from ..models import KPIDefinition, KPIValue


class KPIValueInline(admin.TabularInline):
    model = KPIValue
    extra = 0
    fields = ['period_start', 'period_end', 'value', 'is_on_target', 'variance_from_target']
    readonly_fields = ['is_on_target', 'variance_from_target', 'created_at']
    ordering = ['-period_start']


@admin.register(KPIDefinition)
class KPIDefinitionAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'category', 'unit', 'target_value',
        'higher_is_better', 'aggregation_period', 'show_on_dashboard', 'is_active'
    ]
    list_filter = ['category', 'aggregation_period', 'higher_is_better', 'is_active', 'show_on_dashboard']
    search_fields = ['code', 'name', 'description', 'calculation_method']
    ordering = ['category', 'display_order', 'code']
    readonly_fields = ['public_id', 'created_at', 'created_by', 'updated_at', 'updated_by']
    inlines = [KPIValueInline]

    fieldsets = (
        ('KPI Identification', {
            'fields': ('code', 'name', 'description', 'category')
        }),
        ('Measurement', {
            'fields': ('unit', 'calculation_method', 'aggregation_period', 'decimal_places')
        }),
        ('Targets & Thresholds', {
            'fields': (
                'target_value', 'warning_threshold', 'critical_threshold',
                'higher_is_better'
            )
        }),
        ('Display Settings', {
            'fields': ('display_order', 'show_on_dashboard', 'is_active')
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )


@admin.register(KPIValue)
class KPIValueAdmin(admin.ModelAdmin):
    list_display = [
        'kpi_definition', 'period_start', 'period_end', 'value',
        'status_display', 'is_on_target', 'variance_from_target',
        'customer_name', 'department'
    ]
    list_filter = [
        'kpi_definition', 'is_on_target', 'period_start',
        'customer_name', 'department'
    ]
    search_fields = [
        'kpi_definition__code', 'kpi_definition__name',
        'customer_name', 'notes'
    ]
    date_hierarchy = 'period_start'
    raw_id_fields = ['kpi_definition']
    readonly_fields = [
        'public_id', 'is_on_target', 'variance_from_target', 'status_display',
        'variance_percentage_display',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    fieldsets = (
        ('KPI', {
            'fields': ('kpi_definition',)
        }),
        ('Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Value', {
            'fields': (
                'value', 'is_on_target', 'variance_from_target',
                'variance_percentage_display', 'status_display'
            )
        }),
        ('Context (Optional)', {
            'fields': (
                'job_card_id', 'batch_order_id', 'customer_name',
                'employee_id', 'asset_id', 'department'
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

    def status_display(self, obj):
        status = obj.status
        if status == 'ON_TARGET':
            return format_html('<span style="color: green; font-weight: bold;">✓ On Target</span>')
        if status == 'WARNING':
            return format_html('<span style="color: orange; font-weight: bold;">⚠ Warning</span>')
        if status == 'CRITICAL':
            return format_html('<span style="color: red; font-weight: bold;">✗ Critical</span>')
        return status

    status_display.short_description = 'Status'

    def variance_percentage_display(self, obj):
        pct = obj.variance_percentage
        if pct is None:
            return 'N/A'
        if pct > 0:
            if obj.kpi_definition.higher_is_better:
                return format_html('<span style="color: green;">+{:.2f}%</span>', pct)
            return format_html('<span style="color: red;">+{:.2f}%</span>', pct)
        if pct < 0:
            if obj.kpi_definition.higher_is_better:
                return format_html('<span style="color: red;">{:.2f}%</span>', pct)
            return format_html('<span style="color: green;">{:.2f}%</span>', pct)
        return '0%'

    variance_percentage_display.short_description = 'Variance %'
