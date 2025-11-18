"""
Planning & KPI - Job Metrics, WIP Snapshots, and Delivery Forecasts Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from ..models import JobMetrics, WIPSnapshot, DeliveryForecast


@admin.register(JobMetrics)
class JobMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'job_card_id', 'total_turnaround_hours', 'is_on_time', 'delay_days',
        'rework_count', 'ncr_count', 'cost_variance', 'calculated_at'
    ]
    list_filter = ['is_on_time', 'calculated_at']
    search_fields = ['job_card_id']
    ordering = ['-calculated_at']
    readonly_fields = [
        'public_id', 'calculated_at', 'cost_variance_percentage_display',
        'flow_efficiency_display',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    fieldsets = (
        ('Job Reference', {
            'fields': ('job_card_id',)
        }),
        ('Turnaround Time', {
            'fields': (
                'total_turnaround_hours', 'active_work_hours',
                'waiting_hours', 'queue_hours', 'flow_efficiency_display'
            )
        }),
        ('Quality Metrics', {
            'fields': ('rework_count', 'ncr_count', 'defect_rate', 'first_pass_yield')
        }),
        ('Delivery Performance', {
            'fields': (
                'planned_completion', 'actual_completion',
                'is_on_time', 'delay_days'
            )
        }),
        ('Cost Performance', {
            'fields': (
                'estimated_cost', 'actual_cost', 'cost_variance',
                'cost_variance_percentage_display', 'labor_cost', 'material_cost'
            )
        }),
        ('Efficiency Metrics', {
            'fields': ('efficiency_rate', 'utilization_rate')
        }),
        ('Timestamps', {
            'fields': ('calculated_at',)
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def cost_variance_percentage_display(self, obj):
        pct = obj.cost_variance_percentage
        if pct is None:
            return 'N/A'
        if pct > 10:
            return format_html('<span style="color: red;">+{:.2f}%</span>', pct)
        if pct > 0:
            return format_html('<span style="color: orange;">+{:.2f}%</span>', pct)
        if pct < 0:
            return format_html('<span style="color: green;">{:.2f}%</span>', pct)
        return '0%'

    cost_variance_percentage_display.short_description = 'Cost Variance %'

    def flow_efficiency_display(self, obj):
        eff = obj.flow_efficiency
        if eff is None:
            return 'N/A'
        return f'{eff:.1f}%'

    flow_efficiency_display.short_description = 'Flow Efficiency'

    actions = ['recalculate_cost_variance', 'update_delivery_status']

    def recalculate_cost_variance(self, request, queryset):
        for metrics in queryset:
            metrics.calculate_cost_variance()
        self.message_user(request, f'Recalculated cost variance for {queryset.count()} jobs.')

    recalculate_cost_variance.short_description = 'Recalculate cost variance'

    def update_delivery_status(self, request, queryset):
        for metrics in queryset:
            metrics.update_delivery_status()
        self.message_user(request, f'Updated delivery status for {queryset.count()} jobs.')

    update_delivery_status.short_description = 'Update delivery status'


@admin.register(WIPSnapshot)
class WIPSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'snapshot_time', 'total_jobs_in_wip', 'jobs_on_track', 'jobs_at_risk',
        'jobs_delayed', 'health_score_display', 'total_wip_value'
    ]
    list_filter = ['snapshot_time']
    ordering = ['-snapshot_time']
    readonly_fields = [
        'public_id', 'snapshot_time', 'health_score_display',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    fieldsets = (
        ('Snapshot Time', {
            'fields': ('snapshot_time', 'health_score_display')
        }),
        ('Job Counts', {
            'fields': (
                'total_jobs_in_wip', 'jobs_on_track',
                'jobs_at_risk', 'jobs_delayed'
            )
        }),
        ('By Status', {
            'fields': (
                'jobs_in_evaluation', 'jobs_awaiting_approval',
                'jobs_awaiting_materials', 'jobs_in_production',
                'jobs_under_qc', 'jobs_on_hold'
            )
        }),
        ('Value & Age', {
            'fields': ('total_wip_value', 'avg_age_days', 'max_age_days')
        }),
        ('Bottlenecks', {
            'fields': ('bottleneck_resources_json',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def health_score_display(self, obj):
        score = obj.health_score
        if score >= 80:
            return format_html('<span style="color: green; font-weight: bold;">{:.1f} - Good</span>', score)
        if score >= 60:
            return format_html('<span style="color: orange; font-weight: bold;">{:.1f} - Fair</span>', score)
        return format_html('<span style="color: red; font-weight: bold;">{:.1f} - Poor</span>', score)

    health_score_display.short_description = 'Health Score'


@admin.register(DeliveryForecast)
class DeliveryForecastAdmin(admin.ModelAdmin):
    list_display = [
        'job_card_id', 'customer_required_date', 'forecast_date',
        'potential_delay_days', 'confidence_level', 'at_risk',
        'urgency_display', 'escalation_required'
    ]
    list_filter = [
        'at_risk', 'confidence_level', 'escalation_required',
        'customer_required_date'
    ]
    search_fields = ['job_card_id', 'actions_required', 'escalation_reason']
    date_hierarchy = 'customer_required_date'
    ordering = ['customer_required_date', '-at_risk']
    readonly_fields = [
        'public_id', 'potential_delay_days', 'at_risk', 'escalation_required',
        'days_until_due_display', 'urgency_display', 'calculated_at',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    fieldsets = (
        ('Job Reference', {
            'fields': ('job_card_id', 'batch_order_id')
        }),
        ('Dates', {
            'fields': (
                'customer_required_date', 'forecast_date',
                'days_until_due_display', 'potential_delay_days'
            )
        }),
        ('Risk Assessment', {
            'fields': ('confidence_level', 'at_risk', 'urgency_display')
        }),
        ('Risk Factors', {
            'fields': ('risk_factors_json',)
        }),
        ('Actions', {
            'fields': ('actions_required',)
        }),
        ('Escalation', {
            'fields': ('escalation_required', 'escalation_reason')
        }),
        ('Timestamps', {
            'fields': ('calculated_at',)
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def days_until_due_display(self, obj):
        days = obj.days_until_due
        if days < 0:
            return format_html('<span style="color: red; font-weight: bold;">{} days OVERDUE</span>', abs(days))
        if days <= 7:
            return format_html('<span style="color: red;">{} days</span>', days)
        if days <= 14:
            return format_html('<span style="color: orange;">{} days</span>', days)
        return f'{days} days'

    days_until_due_display.short_description = 'Days Until Due'

    def urgency_display(self, obj):
        level = obj.urgency_level
        if level == 'CRITICAL':
            return format_html('<span style="color: red; font-weight: bold;">CRITICAL</span>')
        if level == 'HIGH':
            return format_html('<span style="color: orange; font-weight: bold;">HIGH</span>')
        if level == 'MEDIUM':
            return format_html('<span style="color: #cc9900;">MEDIUM</span>')
        return format_html('<span style="color: green;">LOW</span>')

    urgency_display.short_description = 'Urgency'
