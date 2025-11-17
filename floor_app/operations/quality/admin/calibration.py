"""
Quality Management - Calibration Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from ..models import CalibratedEquipment, CalibrationRecord


class CalibrationRecordInline(admin.TabularInline):
    model = CalibrationRecord
    extra = 0
    fields = [
        'calibration_date', 'performed_by', 'certificate_number',
        'result', 'next_due_date', 'cost'
    ]
    readonly_fields = ['created_at']
    ordering = ['-calibration_date']


@admin.register(CalibratedEquipment)
class CalibratedEquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'equipment_id', 'name', 'equipment_type', 'status', 'is_critical',
        'last_calibration_date', 'next_calibration_due', 'days_until_due_display'
    ]
    list_filter = [
        'status', 'equipment_type', 'is_critical', 'last_calibration_result'
    ]
    search_fields = [
        'equipment_id', 'name', 'serial_number', 'manufacturer', 'model'
    ]
    ordering = ['equipment_id']
    readonly_fields = [
        'public_id', 'days_until_due_display', 'is_usable_display',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]
    inlines = [CalibrationRecordInline]

    fieldsets = (
        ('Equipment Identification', {
            'fields': (
                'equipment_id', 'name', 'equipment_type',
                'manufacturer', 'model', 'serial_number'
            )
        }),
        ('Calibration Requirements', {
            'fields': (
                'calibration_interval_days', 'calibration_procedure',
                'calibration_standard'
            )
        }),
        ('Current Status', {
            'fields': (
                'status', 'last_calibration_date', 'next_calibration_due',
                'last_calibration_result', 'days_until_due_display', 'is_usable_display'
            )
        }),
        ('Location & Custody', {
            'fields': ('location', 'custodian')
        }),
        ('Certificate Info', {
            'fields': ('certificate_number', 'calibration_lab')
        }),
        ('Importance', {
            'fields': ('is_critical',)
        }),
        ('Purchase Info', {
            'classes': ('collapse',),
            'fields': ('purchase_date', 'warranty_expiry', 'purchase_cost')
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def days_until_due_display(self, obj):
        days = obj.days_until_due
        if days is None:
            return 'N/A'
        if days < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} days OVERDUE</span>',
                abs(days)
            )
        if days <= 30:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{} days</span>',
                days
            )
        return f'{days} days'

    days_until_due_display.short_description = 'Days Until Due'

    def is_usable_display(self, obj):
        if obj.is_usable:
            return format_html('<span style="color: green;">✓ Safe to Use</span>')
        return format_html('<span style="color: red;">✗ DO NOT USE</span>')

    is_usable_display.short_description = 'Usability'

    actions = ['update_calibration_status']

    def update_calibration_status(self, request, queryset):
        for equipment in queryset:
            equipment.update_status()
        self.message_user(request, f'Updated status for {queryset.count()} equipment.')

    update_calibration_status.short_description = 'Update calibration status'


@admin.register(CalibrationRecord)
class CalibrationRecordAdmin(admin.ModelAdmin):
    list_display = [
        'equipment', 'calibration_date', 'performed_by', 'certificate_number',
        'result', 'next_due_date', 'cost'
    ]
    list_filter = ['result', 'calibration_date']
    search_fields = [
        'equipment__equipment_id', 'equipment__name', 'certificate_number',
        'performed_by', 'calibration_lab'
    ]
    date_hierarchy = 'calibration_date'
    raw_id_fields = ['equipment']
    readonly_fields = ['public_id', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        ('Calibration Event', {
            'fields': (
                'equipment', 'calibration_date', 'performed_by',
                'calibration_lab', 'certificate_number'
            )
        }),
        ('Results', {
            'fields': ('result', 'adjustments_made', 'out_of_tolerance_findings')
        }),
        ('Measurements', {
            'fields': ('measurements_json',)
        }),
        ('Next Due', {
            'fields': ('next_due_date', 'cost')
        }),
        ('Certificate Document', {
            'fields': ('certificate_file',)
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )
