"""
Admin configuration for Corrective Maintenance models.
"""
from django.contrib import admin
from floor_app.operations.maintenance.models import (
    MaintenanceRequest,
    WorkOrder,
    WorkOrderAttachment,
    PartsUsage,
)


class WorkOrderAttachmentInline(admin.TabularInline):
    model = WorkOrderAttachment
    extra = 0
    fields = ['title', 'attachment_type', 'file', 'description']
    readonly_fields = ['created_at']


class PartsUsageInline(admin.TabularInline):
    model = PartsUsage
    extra = 0
    fields = ['item_name', 'quantity_used', 'unit_of_measure', 'unit_cost', 'total_cost']
    readonly_fields = ['total_cost']


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_number', 'title', 'asset', 'priority', 'status',
        'requested_by', 'request_date', 'is_production_stopped', 'age_display'
    ]
    list_filter = [
        'status', 'priority', 'is_production_stopped',
        'request_date', 'is_deleted'
    ]
    search_fields = [
        'request_number', 'title', 'description', 'symptoms',
        'asset__asset_code', 'asset__name'
    ]
    ordering = ['-request_date']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'request_date', 'age_display', 'age_in_hours'
    ]
    raw_id_fields = ['asset', 'requested_by', 'reviewed_by', 'work_order']
    date_hierarchy = 'request_date'

    fieldsets = (
        ('Request Info', {
            'fields': (
                'request_number', 'asset', 'title', 'description',
                'symptoms', 'public_id'
            )
        }),
        ('Priority & Status', {
            'fields': ('priority', 'status')
        }),
        ('Requester', {
            'fields': (
                'requested_by', 'request_date', 'age_display',
                'requester_phone', 'requester_location'
            )
        }),
        ('Production Impact', {
            'fields': ('is_production_stopped', 'estimated_downtime_minutes')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'rejection_reason')
        }),
        ('Resulting Work Order', {
            'fields': ('work_order',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'asset', 'requested_by', 'reviewed_by'
        )

    def age_display(self, obj):
        return obj.age_display
    age_display.short_description = 'Age'


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = [
        'wo_number', 'title', 'asset', 'wo_type', 'priority', 'status',
        'assigned_to', 'planned_start', 'is_overdue', 'total_cost'
    ]
    list_filter = [
        'status', 'wo_type', 'priority', 'root_cause_category',
        'planned_start', 'is_deleted'
    ]
    search_fields = [
        'wo_number', 'title', 'problem_description',
        'asset__asset_code', 'asset__name', 'solution_summary'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'total_cost', 'is_overdue', 'age_in_days',
        'estimated_duration_display', 'actual_duration_display'
    ]
    raw_id_fields = [
        'asset', 'assigned_to', 'completed_by', 'cancelled_by', 'follow_up_wo'
    ]
    inlines = [WorkOrderAttachmentInline, PartsUsageInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Identification', {
            'fields': ('wo_number', 'asset', 'title', 'public_id')
        }),
        ('Classification', {
            'fields': ('wo_type', 'priority', 'status')
        }),
        ('Problem', {
            'fields': ('problem_description',)
        }),
        ('Planning', {
            'fields': (
                'planned_start', 'planned_end', 'estimated_duration_minutes',
                'estimated_duration_display'
            )
        }),
        ('Execution', {
            'fields': (
                'actual_start', 'actual_end', 'actual_duration_minutes',
                'actual_duration_display', 'is_overdue', 'age_in_days'
            )
        }),
        ('Assignment', {
            'fields': (
                'assigned_to', 'assigned_at',
                'team_member_ids', 'team_member_names'
            )
        }),
        ('Root Cause Analysis', {
            'fields': ('root_cause_category', 'root_cause_detail')
        }),
        ('Solution', {
            'fields': ('solution_summary', 'actions_taken')
        }),
        ('Follow-up', {
            'fields': (
                'follow_up_required', 'follow_up_notes', 'follow_up_wo'
            )
        }),
        ('Sources', {
            'fields': ('source_pm_task_id',),
            'classes': ('collapse',)
        }),
        ('Costs', {
            'fields': ('labor_cost', 'parts_cost', 'external_cost', 'total_cost')
        }),
        ('Completion', {
            'fields': ('completed_by',)
        }),
        ('Waiting/On-Hold', {
            'fields': ('waiting_reason', 'waiting_since'),
            'classes': ('collapse',)
        }),
        ('Cancellation', {
            'fields': ('cancelled_by', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'asset', 'assigned_to', 'completed_by'
        )

    def total_cost(self, obj):
        return f"{obj.total_cost:,.2f}"
    total_cost.short_description = 'Total Cost'

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'


@admin.register(WorkOrderAttachment)
class WorkOrderAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'work_order', 'title', 'attachment_type',
        'file_extension', 'created_at'
    ]
    list_filter = ['attachment_type', 'is_deleted']
    search_fields = ['title', 'description', 'work_order__wo_number']
    ordering = ['-created_at']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'file_extension', 'file_size_display'
    ]
    raw_id_fields = ['work_order']

    fieldsets = (
        ('Attachment Info', {
            'fields': (
                'work_order', 'title', 'attachment_type', 'file',
                'description', 'file_extension', 'file_size_display'
            )
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def file_extension(self, obj):
        return obj.file_extension
    file_extension.short_description = 'Type'


@admin.register(PartsUsage)
class PartsUsageAdmin(admin.ModelAdmin):
    list_display = [
        'work_order', 'item_name', 'quantity_used', 'unit_of_measure',
        'unit_cost', 'total_cost', 'transaction_type', 'usage_date'
    ]
    list_filter = ['transaction_type', 'usage_date', 'is_deleted']
    search_fields = [
        'work_order__wo_number', 'item_name', 'item_sku', 'notes'
    ]
    ordering = ['-usage_date']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'total_cost', 'usage_date'
    ]
    raw_id_fields = ['work_order', 'used_by']

    fieldsets = (
        ('Usage Info', {
            'fields': ('work_order', 'transaction_type', 'usage_date')
        }),
        ('Item', {
            'fields': ('item_id', 'item_sku', 'item_name')
        }),
        ('Quantity', {
            'fields': ('quantity_used', 'unit_of_measure')
        }),
        ('Source', {
            'fields': ('location_id', 'location_code')
        }),
        ('Cost', {
            'fields': ('unit_cost', 'total_cost')
        }),
        ('Tracking', {
            'fields': ('used_by', 'notes', 'inventory_transaction_id')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('work_order')
