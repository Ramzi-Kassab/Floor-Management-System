"""
Admin interface for Maintenance module.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import *


class AssetDocumentInline(admin.TabularInline):
    model = AssetDocument
    extra = 1
    autocomplete_fields = ['document']


class PMScheduleInline(admin.TabularInline):
    model = PMSchedule
    extra = 0
    readonly_fields = ['last_performed_at', 'is_overdue']
    fields = ['pm_template', 'next_due_date', 'last_performed_at', 'is_active', 'is_overdue']


class WorkOrderNoteInline(admin.TabularInline):
    model = WorkOrderNote
    extra = 1
    readonly_fields = ['created_at', 'created_by']


class WorkOrderPartInline(admin.TabularInline):
    model = WorkOrderPart
    extra = 1


class ProductionImpactInline(admin.StackedInline):
    model = ProductionImpact
    extra = 0


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'default_criticality', 'asset_count', 'is_active']
    search_fields = ['name', 'code', 'description']
    list_filter = ['is_active', 'default_criticality']
    list_editable = ['is_active']


@admin.register(AssetLocation)
class AssetLocationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'full_path', 'is_active']
    search_fields = ['name', 'code']
    list_filter = ['is_active', 'parent']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        'asset_code', 'name', 'category', 'location', 'status_badge',
        'criticality_badge', 'is_critical', 'open_work_orders_count', 'last_pm_date'
    ]
    list_filter = ['status', 'criticality', 'category', 'location', 'is_critical', 'is_deleted']
    search_fields = ['asset_code', 'name', 'serial_number', 'erp_asset_number']
    readonly_fields = ['qr_token', 'public_id', 'age_years', 'warranty_status', 'total_downtime_hours']
    autocomplete_fields = ['category', 'location', 'responsible_department', 'primary_operator']
    inlines = [AssetDocumentInline, PMScheduleInline]
    fieldsets = (
        ('Identification', {
            'fields': ('asset_code', 'name', 'description', 'qr_token', 'public_id')
        }),
        ('Classification', {
            'fields': ('category', 'location', 'status', 'criticality', 'is_critical')
        }),
        ('Equipment Details', {
            'fields': ('manufacturer', 'model_number', 'serial_number', 'year_manufactured'),
            'classes': ['collapse']
        }),
        ('Ownership', {
            'fields': (
                'purchase_date', 'purchase_cost', 'warranty_expires', 'warranty_status',
                'vendor', 'erp_asset_number'
            ),
            'classes': ['collapse']
        }),
        ('Operations', {
            'fields': (
                'installation_date', 'responsible_department', 'primary_operator',
                'meter_reading', 'meter_unit', 'last_pm_date', 'next_pm_date'
            ),
            'classes': ['collapse']
        }),
        ('Flags', {
            'fields': ('requires_certification', 'has_safety_lockout'),
        }),
        ('Technical', {
            'fields': ('specifications', 'notes'),
            'classes': ['collapse']
        }),
    )

    def status_badge(self, obj):
        colors = {
            'IN_SERVICE': '#10b981',
            'UNDER_MAINTENANCE': '#f59e0b',
            'OUT_OF_SERVICE': '#ef4444',
            'SCRAPPED': '#6b7280',
        }
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            colors.get(obj.status, '#6b7280'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def criticality_badge(self, obj):
        colors = {'LOW': '#9ca3af', 'MEDIUM': '#3b82f6', 'HIGH': '#f59e0b', 'CRITICAL': '#ef4444'}
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            colors.get(obj.criticality, '#6b7280'), obj.criticality
        )
    criticality_badge.short_description = 'Criticality'


@admin.register(PMTemplate)
class PMTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'frequency_type', 'frequency_days', 'estimated_duration_minutes',
        'applies_to_category', 'is_active'
    ]
    list_filter = ['frequency_type', 'is_active', 'applies_to_category', 'skill_level_required']
    search_fields = ['code', 'name', 'description']
    filter_horizontal = ['applies_to_assets']
    autocomplete_fields = ['applies_to_category', 'linked_procedure']


@admin.register(PMTask)
class PMTaskAdmin(admin.ModelAdmin):
    list_display = [
        'schedule', 'scheduled_date', 'status', 'performed_by',
        'actual_start', 'actual_end', 'duration_minutes'
    ]
    list_filter = ['status', 'scheduled_date']
    autocomplete_fields = ['performed_by']
    readonly_fields = ['next_due_updated']


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_number', 'title', 'asset', 'priority_badge', 'status_badge',
        'requested_by', 'created_at', 'reviewed_by'
    ]
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['request_number', 'title', 'description']
    readonly_fields = ['request_number', 'reviewed_at']
    autocomplete_fields = ['asset', 'department']

    def priority_badge(self, obj):
        colors = {'LOW': '#9ca3af', 'MEDIUM': '#3b82f6', 'HIGH': '#f59e0b', 'CRITICAL': '#ef4444'}
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            colors.get(obj.priority, '#6b7280'), obj.priority
        )
    priority_badge.short_description = 'Priority'

    def status_badge(self, obj):
        colors = {
            'NEW': '#3b82f6', 'UNDER_REVIEW': '#f59e0b', 'APPROVED': '#10b981',
            'REJECTED': '#ef4444', 'CONVERTED_TO_WO': '#8b5cf6'
        }
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            colors.get(obj.status, '#6b7280'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(MaintenanceWorkOrder)
class MaintenanceWorkOrderAdmin(admin.ModelAdmin):
    list_display = [
        'work_order_number', 'title', 'asset', 'work_order_type', 'priority_badge',
        'status_badge', 'assigned_to', 'planned_start', 'actual_end', 'total_cost'
    ]
    list_filter = ['status', 'priority', 'work_order_type', 'root_cause_category', 'created_at']
    search_fields = ['work_order_number', 'title', 'description']
    readonly_fields = ['work_order_number', 'public_id', 'total_cost']
    autocomplete_fields = ['asset', 'assigned_to', 'completed_by']
    inlines = [WorkOrderNoteInline, WorkOrderPartInline]
    fieldsets = (
        ('Core', {
            'fields': ('work_order_number', 'asset', 'title', 'description', 'work_order_type', 'priority', 'status')
        }),
        ('Scheduling', {
            'fields': (('planned_start', 'planned_end'), ('actual_start', 'actual_end'))
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_team', 'assigned_by', 'assigned_at')
        }),
        ('Problem Analysis', {
            'fields': ('problem_description', 'failure_mode', 'root_cause_category', 'root_cause_detail'),
            'classes': ['collapse']
        }),
        ('Solution', {
            'fields': ('solution_summary', 'work_performed', 'recommendations'),
            'classes': ['collapse']
        }),
        ('Costs', {
            'fields': ('labor_hours', 'labor_cost', 'parts_cost', 'external_cost', 'total_cost'),
            'classes': ['collapse']
        }),
        ('Flags', {
            'fields': ('requires_shutdown', 'safety_permit_required', 'contractor_involved')
        }),
    )

    def priority_badge(self, obj):
        colors = {'LOW': '#9ca3af', 'MEDIUM': '#3b82f6', 'HIGH': '#f59e0b', 'CRITICAL': '#ef4444'}
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            colors.get(obj.priority, '#6b7280'), obj.priority
        )
    priority_badge.short_description = 'Priority'

    def status_badge(self, obj):
        colors = {
            'PLANNED': '#6b7280', 'ASSIGNED': '#3b82f6', 'IN_PROGRESS': '#f59e0b',
            'WAITING_PARTS': '#f97316', 'COMPLETED': '#10b981', 'CANCELLED': '#ef4444'
        }
        return format_html(
            '<span style="background:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            colors.get(obj.status, '#6b7280'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(DowntimeEvent)
class DowntimeEventAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'event_type', 'start_time', 'end_time', 'duration_hours',
        'severity', 'is_planned', 'has_production_impact'
    ]
    list_filter = ['event_type', 'severity', 'is_planned', 'has_production_impact', 'start_time']
    search_fields = ['asset__asset_code', 'reason_description']
    autocomplete_fields = ['asset', 'work_order']
    inlines = [ProductionImpactInline]


@admin.register(ProductionImpact)
class ProductionImpactAdmin(admin.ModelAdmin):
    list_display = [
        'downtime_event', 'impact_type', 'customer_name', 'batch_reference',
        'delay_hours', 'lost_or_delayed_revenue', 'is_revenue_confirmed'
    ]
    list_filter = ['impact_type', 'is_revenue_confirmed', 'created_at']
    search_fields = ['customer_name', 'batch_reference', 'job_card_number']


@admin.register(LostSalesRecord)
class LostSalesRecordAdmin(admin.ModelAdmin):
    list_display = [
        'customer_name', 'order_reference', 'original_order_value',
        'revenue_lost', 'revenue_delayed', 'recovery_possible', 'confirmed_at'
    ]
    list_filter = ['recovery_possible', 'confirmed_at']
    search_fields = ['customer_name', 'order_reference']
    readonly_fields = ['confirmed_at']
