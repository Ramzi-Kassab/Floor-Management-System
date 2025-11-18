"""
Planning & KPI - Schedule Management Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from ..models import ProductionSchedule, ScheduledOperation


class ScheduledOperationInline(admin.TabularInline):
    model = ScheduledOperation
    extra = 0
    fields = [
        'job_card_id', 'operation_code', 'planned_start', 'planned_end',
        'status', 'resource_type'
    ]
    readonly_fields = ['created_at']


@admin.register(ProductionSchedule)
class ProductionScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'schedule_date', 'status', 'scheduling_algorithm',
        'planning_horizon_days', 'operation_count', 'published_at', 'created_by'
    ]
    list_filter = ['status', 'scheduling_algorithm']
    search_fields = ['name', 'notes']
    date_hierarchy = 'schedule_date'
    ordering = ['-schedule_date']
    raw_id_fields = ['created_by', 'published_by']
    readonly_fields = [
        'public_id', 'operation_count', 'is_editable_display',
        'published_at', 'created_at', 'created_by', 'updated_at', 'updated_by'
    ]
    inlines = [ScheduledOperationInline]

    fieldsets = (
        ('Schedule Info', {
            'fields': ('name', 'schedule_date', 'status', 'is_editable_display')
        }),
        ('Planning Parameters', {
            'fields': (
                'planning_horizon_days', 'scheduling_algorithm', 'priority_weighting'
            )
        }),
        ('Workflow', {
            'fields': ('created_by', 'published_at', 'published_by')
        }),
        ('Statistics', {
            'fields': ('operation_count',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def operation_count(self, obj):
        return obj.operation_count

    operation_count.short_description = 'Operations'

    def is_editable_display(self, obj):
        if obj.is_editable:
            return format_html('<span style="color: green;">✓ Editable</span>')
        return format_html('<span style="color: gray;">✗ Locked</span>')

    is_editable_display.short_description = 'Editable'

    actions = ['publish_schedules', 'freeze_schedules']

    def publish_schedules(self, request, queryset):
        count = 0
        for schedule in queryset.filter(status='DRAFT'):
            schedule.publish(request.user)
            count += 1
        self.message_user(request, f'Published {count} schedules.')

    publish_schedules.short_description = 'Publish selected schedules'

    def freeze_schedules(self, request, queryset):
        count = 0
        for schedule in queryset.filter(status='PUBLISHED'):
            schedule.freeze()
            count += 1
        self.message_user(request, f'Froze {count} schedules.')

    freeze_schedules.short_description = 'Freeze selected schedules'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ScheduledOperation)
class ScheduledOperationAdmin(admin.ModelAdmin):
    list_display = [
        'job_card_id', 'operation_code', 'schedule', 'planned_start',
        'planned_end', 'status', 'resource_type', 'is_delayed'
    ]
    list_filter = [
        'status', 'is_delayed', 'delay_category', 'materials_available',
        'resource_type'
    ]
    search_fields = ['job_card_id', 'operation_code', 'delay_reason']
    date_hierarchy = 'planned_start'
    raw_id_fields = ['schedule', 'resource_type']
    readonly_fields = [
        'public_id', 'variance_hours_display', 'is_on_track_display',
        'actual_start', 'actual_end', 'actual_duration_hours',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    fieldsets = (
        ('Schedule Link', {
            'fields': ('schedule',)
        }),
        ('Operation', {
            'fields': ('job_card_id', 'job_route_step_id', 'operation_code')
        }),
        ('Timing', {
            'fields': (
                'planned_start', 'planned_end', 'planned_duration_hours',
                'earliest_start', 'latest_end'
            )
        }),
        ('Resource Assignment', {
            'fields': (
                'resource_type', 'assigned_asset_id', 'assigned_employee_id'
            )
        }),
        ('Priority', {
            'fields': ('sequence_number', 'priority_score')
        }),
        ('Status', {
            'fields': ('status', 'is_on_track_display')
        }),
        ('Actual Execution', {
            'fields': (
                'actual_start', 'actual_end', 'actual_duration_hours',
                'variance_hours_display'
            )
        }),
        ('Delays', {
            'fields': ('is_delayed', 'delay_reason', 'delay_category')
        }),
        ('Materials', {
            'fields': ('materials_available', 'materials_shortage_list')
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def variance_hours_display(self, obj):
        variance = obj.variance_hours
        if variance is None:
            return 'N/A'
        if variance > 0:
            return format_html(
                '<span style="color: red;">+{:.2f} hrs (Over)</span>',
                variance
            )
        if variance < 0:
            return format_html(
                '<span style="color: green;">{:.2f} hrs (Under)</span>',
                variance
            )
        return '0 hrs'

    variance_hours_display.short_description = 'Time Variance'

    def is_on_track_display(self, obj):
        if obj.is_on_track:
            return format_html('<span style="color: green;">✓ On Track</span>')
        return format_html('<span style="color: red;">✗ Off Track</span>')

    is_on_track_display.short_description = 'Status'

    actions = ['start_operations', 'complete_operations']

    def start_operations(self, request, queryset):
        count = 0
        for op in queryset.filter(status__in=['PLANNED', 'RELEASED']):
            op.start_operation()
            count += 1
        self.message_user(request, f'Started {count} operations.')

    start_operations.short_description = 'Start selected operations'

    def complete_operations(self, request, queryset):
        count = 0
        for op in queryset.filter(status='IN_PROGRESS'):
            op.complete_operation()
            count += 1
        self.message_user(request, f'Completed {count} operations.')

    complete_operations.short_description = 'Complete selected operations'
