from django.contrib import admin
from ..models import QCode, ScanLog, Equipment, MaintenanceRequest, Container, MovementLog, ProcessExecution


@admin.register(QCode)
class QCodeAdmin(admin.ModelAdmin):
    list_display = ['token_short', 'qcode_type', 'label', 'is_active', 'scan_count', 'last_scanned_at', 'created_at']
    list_filter = ['qcode_type', 'is_active', 'code_format', 'created_at']
    search_fields = ['token', 'label', 'description']
    readonly_fields = ['token', 'scan_count', 'last_scanned_at', 'last_scanned_by', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Identification', {
            'fields': ('token', 'qcode_type', 'label', 'description', 'code_format')
        }),
        ('Target', {
            'fields': ('content_type', 'object_id')
        }),
        ('Status', {
            'fields': ('is_active', 'version', 'deactivated_at', 'deactivated_by', 'deactivation_reason')
        }),
        ('Statistics', {
            'fields': ('scan_count', 'last_scanned_at', 'last_scanned_by')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def token_short(self, obj):
        return obj.token_short
    token_short.short_description = 'Token'


@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = ['qcode', 'action_type', 'scanner_display_name', 'success', 'scan_timestamp']
    list_filter = ['action_type', 'success', 'scanner_device_type', 'scan_timestamp']
    search_fields = ['qcode__token', 'scanner_employee_name', 'message']
    readonly_fields = ['qcode', 'scan_timestamp', 'scanner_user', 'scanner_ip']
    ordering = ['-scan_timestamp']
    date_hierarchy = 'scan_timestamp'

    def scanner_display_name(self, obj):
        return obj.scanner_display_name
    scanner_display_name.short_description = 'Scanned By'


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'equipment_type', 'status', 'location_name', 'next_maintenance_date']
    list_filter = ['equipment_type', 'status', 'department_name']
    search_fields = ['code', 'name', 'serial_number', 'manufacturer']
    ordering = ['code']

    fieldsets = (
        ('Basic Info', {
            'fields': ('code', 'name', 'description', 'equipment_type')
        }),
        ('Manufacturer', {
            'fields': ('manufacturer', 'model_number', 'serial_number')
        }),
        ('Location', {
            'fields': ('location_id', 'location_name', 'department_id', 'department_name')
        }),
        ('Status', {
            'fields': ('status', 'qcode_id')
        }),
        ('Maintenance', {
            'fields': ('last_maintenance_date', 'next_maintenance_date', 'maintenance_interval_days')
        }),
        ('Financial', {
            'fields': ('purchase_date', 'purchase_cost', 'current_value', 'warranty_expiry_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'title', 'priority', 'status', 'reported_by_name', 'reported_at']
    list_filter = ['priority', 'status', 'maintenance_type', 'reported_at']
    search_fields = ['title', 'description', 'equipment__code', 'equipment__name']
    ordering = ['-reported_at']
    date_hierarchy = 'reported_at'


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'container_type', 'status', 'current_count', 'location_name']
    list_filter = ['container_type', 'status']
    search_fields = ['code', 'name']
    ordering = ['code']


@admin.register(MovementLog)
class MovementLogAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'movement_type', 'quantity', 'from_location_name', 'to_location_name', 'moved_by_name', 'moved_at']
    list_filter = ['movement_type', 'verified', 'moved_at']
    search_fields = ['item_sku', 'item_name', 'job_card_number']
    ordering = ['-moved_at']
    date_hierarchy = 'moved_at'


@admin.register(ProcessExecution)
class ProcessExecutionAdmin(admin.ModelAdmin):
    list_display = ['operation_name', 'status', 'operator_name', 'start_time', 'end_time', 'duration_minutes']
    list_filter = ['status', 'start_time']
    search_fields = ['operation_name', 'operator_name', 'job_card_id']
    ordering = ['-start_time']
    date_hierarchy = 'start_time'

    def duration_minutes(self, obj):
        return f"{obj.duration_minutes:.1f}" if obj.duration_minutes else "-"
    duration_minutes.short_description = 'Duration (min)'
