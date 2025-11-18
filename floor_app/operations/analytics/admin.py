"""
Admin configuration for Analytics models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    UserSession, PageView, UserActivity, ModuleUsage,
    SystemMetric, ErrorLog, SearchQuery, DailyStatistics
)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'logout_time', 'duration_display', 'device_type', 'browser', 'is_active', 'ip_address']
    list_filter = ['is_active', 'device_type', 'browser', 'operating_system', 'login_time']
    search_fields = ['user__username', 'user__email', 'ip_address', 'session_key']
    readonly_fields = ['session_key', 'login_time', 'last_activity', 'duration_seconds', 'user_agent']
    date_hierarchy = 'login_time'

    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'session_key', 'is_active')
        }),
        ('Time Tracking', {
            'fields': ('login_time', 'last_activity', 'logout_time', 'duration_seconds')
        }),
        ('Device & Browser', {
            'fields': ('device_type', 'browser', 'operating_system', 'user_agent')
        }),
        ('Network', {
            'fields': ('ip_address', 'country', 'city')
        }),
    )

    def duration_display(self, obj):
        return obj.get_duration_display()
    duration_display.short_description = 'Duration'

    def has_add_permission(self, request):
        return False  # Sessions are created automatically


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'url_name', 'module', 'timestamp', 'load_time_badge']
    list_filter = ['module', 'timestamp']
    search_fields = ['user__username', 'url', 'url_name']
    readonly_fields = ['session', 'user', 'url', 'url_name', 'module', 'view_name', 'timestamp', 'referrer', 'load_time_ms', 'query_params']
    date_hierarchy = 'timestamp'

    def load_time_badge(self, obj):
        if obj.load_time_ms is None:
            return '-'
        color = 'green' if obj.load_time_ms < 500 else 'orange' if obj.load_time_ms < 1000 else 'red'
        return format_html('<span style="color: {}">{} ms</span>', color, obj.load_time_ms)
    load_time_badge.short_description = 'Load Time'

    def has_add_permission(self, request):
        return False


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'module', 'description_short', 'timestamp', 'success_badge']
    list_filter = ['action_type', 'module', 'success', 'timestamp']
    search_fields = ['user__username', 'description', 'module']
    readonly_fields = ['session', 'user', 'action_type', 'module', 'description', 'content_type', 'object_id', 'timestamp', 'metadata', 'success', 'error_message']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Activity Information', {
            'fields': ('user', 'session', 'action_type', 'module', 'description')
        }),
        ('Target Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Status', {
            'fields': ('success', 'error_message', 'timestamp')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )

    def description_short(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Description'

    def success_badge(self, obj):
        color = 'green' if obj.success else 'red'
        text = '✓ Success' if obj.success else '✗ Failed'
        return format_html('<span style="color: {}">{}</span>', color, text)
    success_badge.short_description = 'Status'

    def has_add_permission(self, request):
        return False


@admin.register(ModuleUsage)
class ModuleUsageAdmin(admin.ModelAdmin):
    list_display = ['module', 'date', 'page_views', 'unique_users', 'total_actions', 'avg_load_time_ms']
    list_filter = ['module', 'date']
    search_fields = ['module']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

    def has_add_permission(self, request):
        return False


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'unit', 'timestamp']
    list_filter = ['metric_type', 'timestamp']
    readonly_fields = ['metric_type', 'value', 'unit', 'timestamp', 'metadata']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['severity_badge', 'error_type', 'module', 'user', 'timestamp', 'resolved_badge']
    list_filter = ['severity', 'module', 'is_resolved', 'timestamp']
    search_fields = ['error_type', 'error_message', 'module', 'user__username']
    readonly_fields = ['session', 'user', 'severity', 'error_type', 'error_message', 'url', 'module', 'view_name', 'traceback', 'timestamp', 'request_data', 'user_agent', 'ip_address']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Error Information', {
            'fields': ('severity', 'error_type', 'error_message', 'timestamp')
        }),
        ('Context', {
            'fields': ('user', 'session', 'url', 'module', 'view_name')
        }),
        ('Technical Details', {
            'fields': ('traceback', 'request_data', 'user_agent', 'ip_address'),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_at', 'resolved_by', 'resolution_notes')
        }),
    )

    def severity_badge(self, obj):
        colors = {
            'debug': 'gray',
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_severity_display().upper()
        )
    severity_badge.short_description = 'Severity'

    def resolved_badge(self, obj):
        if obj.is_resolved:
            return format_html('<span style="color: green;">✓ Resolved</span>')
        return format_html('<span style="color: red;">✗ Unresolved</span>')
    resolved_badge.short_description = 'Status'

    def has_add_permission(self, request):
        return False


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['user', 'search_term', 'module', 'results_count', 'clicked_result', 'timestamp']
    list_filter = ['module', 'clicked_result', 'timestamp']
    search_fields = ['user__username', 'search_term', 'module']
    readonly_fields = ['user', 'session', 'module', 'search_term', 'filters_applied', 'results_count', 'timestamp', 'clicked_result']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False


@admin.register(DailyStatistics)
class DailyStatisticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'active_users', 'total_logins', 'total_page_views', 'total_actions', 'total_errors']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['date', 'total_users', 'active_users', 'new_users', 'total_logins', 'total_page_views',
                      'total_actions', 'avg_session_duration_seconds', 'avg_page_load_time_ms', 'total_errors',
                      'critical_errors', 'module_statistics', 'peak_concurrent_users', 'peak_hour',
                      'created_at', 'updated_at']

    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('User Metrics', {
            'fields': ('total_users', 'active_users', 'new_users')
        }),
        ('Activity Metrics', {
            'fields': ('total_logins', 'total_page_views', 'total_actions')
        }),
        ('Performance Metrics', {
            'fields': ('avg_session_duration_seconds', 'avg_page_load_time_ms')
        }),
        ('Error Metrics', {
            'fields': ('total_errors', 'critical_errors')
        }),
        ('Module Breakdown', {
            'fields': ('module_statistics',),
            'classes': ('collapse',)
        }),
        ('Peak Usage', {
            'fields': ('peak_concurrent_users', 'peak_hour')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['generate_statistics']

    def generate_statistics(self, request, queryset):
        """Regenerate statistics for selected dates"""
        from .models import DailyStatistics
        count = 0
        for stat in queryset:
            DailyStatistics.generate_for_date(stat.date)
            count += 1
        self.message_user(request, f"Successfully regenerated statistics for {count} date(s).")
    generate_statistics.short_description = "Regenerate statistics for selected dates"
