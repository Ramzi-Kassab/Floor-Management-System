"""
Quality Management - NCR Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from ..models import NonconformanceReport, NCRRootCauseAnalysis, NCRCorrectiveAction


class NCRRootCauseAnalysisInline(admin.TabularInline):
    model = NCRRootCauseAnalysis
    extra = 0
    fields = ['category', 'why_1', 'root_cause_statement', 'is_systemic', 'analyzed_by']
    readonly_fields = ['analyzed_by', 'analyzed_at']


class NCRCorrectiveActionInline(admin.TabularInline):
    model = NCRCorrectiveAction
    extra = 0
    fields = ['action_type', 'description', 'assigned_to', 'due_date', 'status', 'completed_date']


@admin.register(NonconformanceReport)
class NonconformanceReportAdmin(admin.ModelAdmin):
    list_display = [
        'ncr_number', 'title', 'ncr_type', 'status', 'severity',
        'disposition', 'days_open_display', 'target_closure_date', 'reported_by'
    ]
    list_filter = [
        'status', 'ncr_type', 'severity', 'disposition',
        'customer_impact', 'production_impact', 'safety_impact', 'defect_category'
    ]
    search_fields = [
        'ncr_number', 'title', 'description', 'detection_point'
    ]
    date_hierarchy = 'reported_at'
    ordering = ['-reported_at']
    readonly_fields = [
        'public_id', 'ncr_number', 'days_open_display', 'is_overdue_display',
        'created_at', 'created_by', 'updated_at', 'updated_by',
        'reported_at', 'disposition_at', 'actual_closure_date'
    ]
    raw_id_fields = ['reported_by', 'assigned_to', 'disposition_by', 'closed_by']
    inlines = [NCRRootCauseAnalysisInline, NCRCorrectiveActionInline]

    fieldsets = (
        ('NCR Identification', {
            'fields': ('ncr_number', 'ncr_type', 'status', 'title')
        }),
        ('What is Nonconforming', {
            'fields': ('job_card_id', 'serial_unit_id', 'batch_order_id')
        }),
        ('Defect Details', {
            'fields': (
                'defect_category', 'description', 'detection_point',
                'detection_method', 'quantity_affected', 'quantity_contained'
            )
        }),
        ('Severity & Impact', {
            'fields': (
                'severity', 'customer_impact', 'production_impact', 'safety_impact'
            )
        }),
        ('Disposition', {
            'fields': (
                'disposition', 'disposition_reason', 'disposition_by', 'disposition_at'
            )
        }),
        ('Cost Impact', {
            'fields': ('estimated_cost_impact', 'actual_cost_impact', 'lost_revenue')
        }),
        ('Workflow', {
            'fields': (
                'reported_by', 'reported_at', 'assigned_to',
                'target_closure_date', 'actual_closure_date', 'closed_by'
            )
        }),
        ('Status Indicators', {
            'fields': ('days_open_display', 'is_overdue_display')
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def days_open_display(self, obj):
        return obj.days_open

    days_open_display.short_description = 'Days Open'

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">OVERDUE</span>')
        return format_html('<span style="color: green;">On Track</span>')

    is_overdue_display.short_description = 'Overdue Status'

    def save_model(self, request, obj, form, change):
        if not change and not obj.ncr_number:
            obj.ncr_number = NonconformanceReport.generate_ncr_number()
        if not obj.reported_by_id:
            obj.reported_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'defect_category', 'reported_by', 'assigned_to'
        )


@admin.register(NCRRootCauseAnalysis)
class NCRRootCauseAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'ncr', 'category', 'root_cause_statement', 'is_systemic',
        'analyzed_by', 'analyzed_at'
    ]
    list_filter = ['category', 'is_systemic']
    search_fields = ['ncr__ncr_number', 'root_cause_statement', 'why_1', 'why_5']
    raw_id_fields = ['ncr', 'analyzed_by']
    readonly_fields = ['public_id', 'analyzed_at', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        ('NCR Link', {
            'fields': ('ncr', 'category')
        }),
        ('5-Why Analysis', {
            'fields': ('why_1', 'why_2', 'why_3', 'why_4', 'why_5')
        }),
        ('Root Cause', {
            'fields': ('root_cause_statement', 'is_systemic')
        }),
        ('Analysis Info', {
            'fields': ('analyzed_by', 'analyzed_at')
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.analyzed_by_id:
            obj.analyzed_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(NCRCorrectiveAction)
class NCRCorrectiveActionAdmin(admin.ModelAdmin):
    list_display = [
        'ncr', 'action_type', 'description_short', 'assigned_to',
        'due_date', 'status', 'is_overdue_display'
    ]
    list_filter = ['action_type', 'status', 'effectiveness_verified']
    search_fields = ['ncr__ncr_number', 'description', 'completion_notes']
    date_hierarchy = 'due_date'
    raw_id_fields = ['ncr', 'assigned_to', 'verified_by']
    readonly_fields = [
        'public_id', 'is_overdue_display', 'verified_at',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    fieldsets = (
        ('Action Details', {
            'fields': ('ncr', 'action_type', 'description')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'due_date', 'status')
        }),
        ('Completion', {
            'fields': ('completed_date', 'completion_notes')
        }),
        ('Verification', {
            'fields': (
                'effectiveness_verified', 'verification_notes',
                'verified_by', 'verified_at'
            )
        }),
        ('Status', {
            'fields': ('is_overdue_display',)
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def description_short(self, obj):
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description

    description_short.short_description = 'Description'

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">OVERDUE</span>')
        return format_html('<span style="color: green;">OK</span>')

    is_overdue_display.short_description = 'Overdue?'
