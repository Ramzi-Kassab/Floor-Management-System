"""
Analytics Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from floor_app.operations.analytics.models import (
    AppEvent,
    EventSummary,
    InformationRequest,
    RequestTrend,
    AutomationRule,
    AutomationRuleExecution,
    RuleTemplate,
)


@admin.register(AppEvent)
class AppEventAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user', 'event_type', 'view_name',
        'event_category', 'duration_ms', 'http_method'
    ]
    list_filter = [
        'event_type', 'event_category', 'http_method',
        'timestamp'
    ]
    search_fields = [
        'view_name', 'http_path', 'user__username'
    ]
    readonly_fields = [
        'user', 'event_type', 'view_name', 'event_category',
        'http_path', 'http_method', 'timestamp', 'duration_ms',
        'client_ip', 'user_agent', 'metadata'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(EventSummary)
class EventSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'period_type', 'period_start', 'view_name',
        'event_category', 'event_count', 'unique_users'
    ]
    list_filter = ['period_type', 'event_category']
    search_fields = ['view_name']
    readonly_fields = [
        'period_type', 'period_start', 'period_end',
        'event_type', 'view_name', 'event_category',
        'event_count', 'unique_users', 'avg_duration_ms'
    ]
    date_hierarchy = 'period_start'
    ordering = ['-period_start']


@admin.register(InformationRequest)
class InformationRequestAdmin(admin.ModelAdmin):
    list_display = [
        'summary', 'requester', 'channel', 'request_category',
        'status', 'is_repeated', 'request_datetime', 'covered_status'
    ]
    list_filter = [
        'status', 'channel', 'request_category',
        'is_repeated', 'is_now_covered_by_system'
    ]
    search_fields = [
        'summary', 'details', 'requester_name', 'requester_email'
    ]
    readonly_fields = [
        'request_datetime', 'created_at', 'updated_at', 'covered_since'
    ]
    date_hierarchy = 'request_datetime'
    ordering = ['-request_datetime']

    fieldsets = (
        ('Request Information', {
            'fields': (
                'requester', 'requester_name', 'requester_email', 'requester_role',
                'channel', 'request_datetime', 'summary', 'details',
                'request_category', 'priority'
            )
        }),
        ('Related Objects', {
            'fields': (
                'related_job_card', 'related_serial_unit', 'related_customer'
            )
        }),
        ('Frequency', {
            'fields': (
                'is_repeated', 'repeat_count', 'similar_requests'
            )
        }),
        ('System Coverage', {
            'fields': (
                'status', 'is_now_covered_by_system', 'covered_by_view_name',
                'covered_by_url', 'covered_since'
            )
        }),
        ('Response', {
            'fields': (
                'response_time_minutes', 'response_notes'
            )
        }),
        ('Metadata', {
            'fields': (
                'tags', 'created_at', 'updated_at'
            )
        }),
    )

    def covered_status(self, obj):
        if obj.is_now_covered_by_system:
            return format_html('<span style="color: green;">✓ Covered</span>')
        else:
            return format_html('<span style="color: red;">✗ Not Covered</span>')
    covered_status.short_description = 'Covered?'


@admin.register(RequestTrend)
class RequestTrendAdmin(admin.ModelAdmin):
    list_display = [
        'period_type', 'period_start', 'request_category',
        'total_requests', 'covered_requests', 'open_requests'
    ]
    list_filter = ['period_type', 'request_category']
    readonly_fields = [
        'period_type', 'period_start', 'period_end', 'request_category',
        'total_requests', 'covered_requests', 'open_requests',
        'repeated_requests', 'avg_response_time_minutes'
    ]
    date_hierarchy = 'period_start'
    ordering = ['-period_start']


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = [
        'rule_code', 'name', 'rule_scope', 'severity',
        'is_active', 'is_approved', 'trigger_mode',
        'last_run_status', 'total_triggers'
    ]
    list_filter = [
        'rule_scope', 'severity', 'is_active', 'is_approved',
        'trigger_mode', 'action_type'
    ]
    search_fields = ['rule_code', 'name', 'description']
    readonly_fields = [
        'created_at', 'updated_at', 'last_run_at',
        'last_status', 'last_error', 'total_executions', 'total_triggers'
    ]
    ordering = ['rule_scope', 'name']

    fieldsets = (
        ('Identification', {
            'fields': ('name', 'rule_code', 'description', 'tags')
        }),
        ('Scope & Target', {
            'fields': ('rule_scope', 'target_model')
        }),
        ('Condition', {
            'fields': ('condition_definition',),
            'description': 'JSON structure defining when this rule triggers'
        }),
        ('Action', {
            'fields': ('action_type', 'action_config', 'severity')
        }),
        ('Trigger Configuration', {
            'fields': ('trigger_mode', 'schedule_cron', 'event_trigger')
        }),
        ('Control', {
            'fields': (
                'is_active', 'is_approved', 'approved_by', 'approved_at',
                'min_interval_seconds', 'max_triggers_per_day'
            )
        }),
        ('Execution Status', {
            'fields': (
                'last_run_at', 'last_status', 'last_error',
                'total_executions', 'total_triggers'
            )
        }),
        ('Metadata', {
            'fields': ('notes', 'created_at', 'updated_at', 'created_by')
        }),
    )

    def last_run_status(self, obj):
        if obj.last_status == 'success':
            color = 'green'
        elif obj.last_status == 'error':
            color = 'red'
        else:
            color = 'gray'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.last_status or 'Never run'
        )
    last_run_status.short_description = 'Last Status'

    actions = ['activate_rules', 'deactivate_rules', 'run_rules_now']

    def activate_rules(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} rules activated')
    activate_rules.short_description = 'Activate selected rules'

    def deactivate_rules(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} rules deactivated')
    deactivate_rules.short_description = 'Deactivate selected rules'

    def run_rules_now(self, request, queryset):
        results = []
        for rule in queryset:
            try:
                execution = rule.execute()
                results.append(f"{rule.rule_code}: {'TRIGGERED' if execution.was_triggered else 'NO_TRIGGER'}")
            except Exception as e:
                results.append(f"{rule.rule_code}: ERROR - {str(e)}")
        self.message_user(request, '; '.join(results))
    run_rules_now.short_description = 'Run selected rules now'


@admin.register(AutomationRuleExecution)
class AutomationRuleExecutionAdmin(admin.ModelAdmin):
    list_display = [
        'executed_at', 'rule', 'was_triggered',
        'action_executed', 'target_display', 'execution_duration_ms'
    ]
    list_filter = [
        'was_triggered', 'action_executed', 'executed_at', 'rule__rule_scope'
    ]
    search_fields = ['rule__rule_code', 'rule__name', 'comment']
    readonly_fields = [
        'rule', 'executed_at', 'was_triggered', 'context_data',
        'comment', 'action_executed', 'action_result', 'action_error',
        'execution_duration_ms'
    ]
    date_hierarchy = 'executed_at'
    ordering = ['-executed_at']

    def target_display(self, obj):
        if obj.target_object:
            return str(obj.target_object)
        return '-'
    target_display.short_description = 'Target'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RuleTemplate)
class RuleTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'template_name', 'rule_scope', 'usage_count', 'is_active'
    ]
    list_filter = ['rule_scope', 'is_active']
    search_fields = ['template_name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['rule_scope', 'template_name']

    fieldsets = (
        ('Template Info', {
            'fields': ('template_name', 'description', 'rule_scope', 'is_active')
        }),
        ('Template Definition', {
            'fields': ('template_definition',),
            'description': 'JSON structure with placeholders'
        }),
        ('Usage', {
            'fields': ('usage_count', 'created_at', 'updated_at')
        }),
    )
