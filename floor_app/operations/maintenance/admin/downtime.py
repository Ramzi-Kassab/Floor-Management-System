"""
Admin configuration for Downtime and Impact models.
"""
from django.contrib import admin
from floor_app.operations.maintenance.models import (
    DowntimeEvent,
    ProductionImpact,
    LostSales,
)


class ProductionImpactInline(admin.TabularInline):
    model = ProductionImpact
    extra = 0
    fields = [
        'batch_order_number', 'job_card_number', 'delay_minutes',
        'impact_description', 'rework_required', 'scrap_generated'
    ]


class LostSalesInline(admin.TabularInline):
    model = LostSales
    fk_name = 'downtime_event'
    extra = 0
    fields = [
        'impact_type', 'customer_name', 'lost_or_delayed_revenue',
        'currency', 'is_confirmed'
    ]


@admin.register(DowntimeEvent)
class DowntimeEventAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'downtime_type', 'reason_category', 'start_time',
        'end_time', 'duration_display', 'production_affected',
        'severity_score', 'is_verified'
    ]
    list_filter = [
        'downtime_type', 'reason_category', 'production_affected',
        'is_verified', 'start_time', 'is_deleted'
    ]
    search_fields = [
        'asset__asset_code', 'asset__name', 'reason_detail', 'notes'
    ]
    ordering = ['-start_time']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'duration_minutes', 'is_ongoing', 'duration_display', 'duration_hours'
    ]
    raw_id_fields = ['asset', 'work_order', 'reported_by', 'verified_by']
    inlines = [ProductionImpactInline, LostSalesInline]
    date_hierarchy = 'start_time'

    fieldsets = (
        ('Event Info', {
            'fields': ('asset', 'work_order', 'public_id')
        }),
        ('Timing', {
            'fields': (
                'start_time', 'end_time', 'duration_minutes',
                'is_ongoing', 'duration_display', 'duration_hours'
            )
        }),
        ('Classification', {
            'fields': (
                'downtime_type', 'reason_category', 'reason_detail'
            )
        }),
        ('Impact Assessment', {
            'fields': ('production_affected', 'severity_score')
        }),
        ('Reporting', {
            'fields': ('reported_by', 'notes')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verified_at')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset', 'work_order')

    def duration_display(self, obj):
        return obj.duration_display
    duration_display.short_description = 'Duration'

    def is_ongoing(self, obj):
        return obj.is_ongoing
    is_ongoing.boolean = True
    is_ongoing.short_description = 'Ongoing'


@admin.register(ProductionImpact)
class ProductionImpactAdmin(admin.ModelAdmin):
    list_display = [
        'downtime_event', 'batch_order_number', 'job_card_number',
        'delay_minutes', 'units_affected', 'rework_required', 'scrap_generated'
    ]
    list_filter = ['rework_required', 'scrap_generated', 'is_deleted']
    search_fields = [
        'batch_order_number', 'job_card_number', 'impact_description'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'delay_display'
    ]
    raw_id_fields = ['downtime_event']

    fieldsets = (
        ('Impact Info', {
            'fields': ('downtime_event', 'public_id')
        }),
        ('Production Reference', {
            'fields': (
                'batch_order_id', 'batch_order_number',
                'job_card_id', 'job_card_number'
            )
        }),
        ('Delay', {
            'fields': (
                'delay_minutes', 'delay_display',
                'planned_completion', 'actual_completion'
            )
        }),
        ('Impact Details', {
            'fields': (
                'impact_description', 'units_affected',
                'rework_required', 'scrap_generated'
            )
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('downtime_event')

    def delay_display(self, obj):
        return obj.delay_display
    delay_display.short_description = 'Delay'


@admin.register(LostSales)
class LostSalesAdmin(admin.ModelAdmin):
    list_display = [
        'impact_type', 'customer_name', 'batch_order_number',
        'lost_or_delayed_revenue', 'currency', 'is_confirmed',
        'net_impact', 'created_at'
    ]
    list_filter = ['impact_type', 'currency', 'is_confirmed', 'is_deleted']
    search_fields = [
        'customer_name', 'batch_order_number', 'notes', 'calculation_basis'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'net_impact'
    ]
    raw_id_fields = ['downtime_event', 'production_impact', 'approved_by']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Lost Sales Info', {
            'fields': ('public_id',)
        }),
        ('Links', {
            'fields': ('downtime_event', 'production_impact')
        }),
        ('Order/Customer', {
            'fields': (
                'batch_order_id', 'batch_order_number',
                'customer_id', 'customer_name'
            )
        }),
        ('Impact Type', {
            'fields': ('impact_type',)
        }),
        ('Delivery', {
            'fields': (
                'expected_delivery_date', 'actual_delivery_date', 'delay_days'
            )
        }),
        ('Financial Impact', {
            'fields': (
                'lost_or_delayed_revenue', 'currency', 'is_confirmed',
                'recovered_amount', 'net_impact'
            )
        }),
        ('Justification', {
            'fields': ('calculation_basis', 'notes')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'downtime_event', 'production_impact'
        )

    def net_impact(self, obj):
        return f"{obj.net_impact:,.2f} {obj.currency}"
    net_impact.short_description = 'Net Impact'
