"""
Admin configuration for Preventive Maintenance models.
"""
from django.contrib import admin
from floor_app.operations.maintenance.models import (
    PMTemplate,
    PMSchedule,
    PMTask,
)


class PMScheduleInline(admin.TabularInline):
    model = PMSchedule
    extra = 0
    fields = ['asset', 'next_due_date', 'last_completed_date', 'is_active']
    readonly_fields = ['last_completed_date']
    raw_id_fields = ['asset']


@admin.register(PMTemplate)
class PMPlanAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'frequency_display', 'estimated_duration_display',
        'priority', 'is_active', 'applies_to_category'
    ]
    list_filter = [
        'is_active', 'frequency_type', 'priority',
        'applies_to_category', 'is_deleted'
    ]
    search_fields = ['code', 'name', 'description', 'tasks_description']
    ordering = ['code']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'frequency_display', 'estimated_duration_display'
    ]
    raw_id_fields = ['applies_to_category']
    filter_horizontal = ['applies_to_specific_assets']
    inlines = [PMScheduleInline]

    fieldsets = (
        ('Identification', {
            'fields': ('code', 'name', 'description', 'public_id')
        }),
        ('Tasks & Instructions', {
            'fields': (
                'tasks_description', 'safety_instructions',
                'tools_required', 'spare_parts_list'
            )
        }),
        ('Requirements', {
            'fields': (
                'required_skill_level', 'minimum_technicians',
                'estimated_duration_minutes', 'estimated_duration_display'
            )
        }),
        ('Priority', {
            'fields': ('priority',)
        }),
        ('Frequency', {
            'fields': (
                'frequency_type', 'interval_days', 'interval_meter_value',
                'frequency_display'
            )
        }),
        ('Scope', {
            'fields': ('applies_to_category', 'applies_to_specific_assets')
        }),
        ('Control', {
            'fields': ('is_active', 'generate_days_before')
        }),
        ('References', {
            'fields': ('instruction_document_id',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def frequency_display(self, obj):
        return obj.frequency_display
    frequency_display.short_description = 'Frequency'

    def estimated_duration_display(self, obj):
        return obj.estimated_duration_display
    estimated_duration_display.short_description = 'Est. Duration'


@admin.register(PMSchedule)
class PMScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'pm_plan', 'next_due_date', 'last_completed_date',
        'days_until_due', 'is_overdue', 'is_active'
    ]
    list_filter = ['is_active', 'pm_plan', 'is_deleted']
    search_fields = ['asset__asset_code', 'asset__name', 'pm_plan__code']
    ordering = ['next_due_date']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'is_overdue', 'days_until_due', 'status_display'
    ]
    raw_id_fields = ['asset', 'pm_plan']
    date_hierarchy = 'next_due_date'

    fieldsets = (
        ('Schedule Info', {
            'fields': ('asset', 'pm_plan', 'public_id')
        }),
        ('Timing', {
            'fields': (
                'next_due_date', 'last_completed_date',
                'days_until_due', 'is_overdue', 'status_display'
            )
        }),
        ('Meter-Based', {
            'fields': ('next_due_meter_reading', 'last_meter_reading_at_pm'),
            'classes': ('collapse',)
        }),
        ('Control', {
            'fields': ('is_active', 'custom_interval_days', 'notes')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset', 'pm_plan')

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'

    def days_until_due(self, obj):
        return obj.days_until_due
    days_until_due.short_description = 'Days Until Due'

    def status_display(self, obj):
        return obj.status_display
    status_display.short_description = 'Status'


@admin.register(PMTask)
class PMTaskAdmin(admin.ModelAdmin):
    list_display = [
        'task_number', 'asset', 'pm_plan', 'scheduled_date',
        'status', 'priority', 'assigned_to', 'is_overdue'
    ]
    list_filter = ['status', 'priority', 'scheduled_date', 'is_deleted']
    search_fields = [
        'task_number', 'schedule__asset__asset_code',
        'schedule__pm_plan__code', 'performed_by_name'
    ]
    ordering = ['-scheduled_date', '-created_at']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'asset', 'pm_plan', 'is_overdue', 'actual_duration_minutes'
    ]
    raw_id_fields = ['schedule', 'assigned_to']
    date_hierarchy = 'scheduled_date'

    fieldsets = (
        ('Task Info', {
            'fields': (
                'task_number', 'schedule', 'asset', 'pm_plan', 'public_id'
            )
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'is_overdue')
        }),
        ('Timing', {
            'fields': (
                'scheduled_date', 'due_date', 'actual_start',
                'actual_end', 'actual_duration_minutes'
            )
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'performed_by_id', 'performed_by_name')
        }),
        ('Results', {
            'fields': (
                'completion_notes', 'issues_found',
                'follow_up_required', 'follow_up_notes'
            )
        }),
        ('Meter Reading', {
            'fields': ('meter_reading_at_completion',),
            'classes': ('collapse',)
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'schedule', 'schedule__asset', 'schedule__pm_plan', 'assigned_to'
        )

    def asset(self, obj):
        return obj.asset.asset_code
    asset.short_description = 'Asset'

    def pm_plan(self, obj):
        return obj.pm_plan.code
    pm_plan.short_description = 'PM Plan'

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'
