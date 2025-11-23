"""
Admin interface for core audit and monitoring models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AuditLog, ChangeHistory, ActivityLog, SystemEvent


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog"""

    list_display = [
        'timestamp',
        'username_display',
        'action_badge',
        'model_name',
        'object_repr',
        'field_name',
        'ip_address',
        'message_preview',
    ]

    list_filter = [
        'action',
        'model_name',
        'timestamp',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'username',
        'model_name',
        'object_repr',
        'message',
        'field_name',
        'old_value',
        'new_value',
    ]

    readonly_fields = [
        'user',
        'username',
        'content_type',
        'object_id',
        'model_name',
        'object_repr',
        'action',
        'field_name',
        'old_value_display',
        'new_value_display',
        'timestamp',
        'ip_address',
        'user_agent_display',
        'session_key',
        'message',
        'extra_data_display',
    ]

    fieldsets = [
        ('Who', {
            'fields': ['user', 'username', 'ip_address', 'session_key']
        }),
        ('What', {
            'fields': [
                'action',
                'model_name',
                'object_repr',
                'content_type',
                'object_id',
            ]
        }),
        ('Changes', {
            'fields': ['field_name', 'old_value_display', 'new_value_display']
        }),
        ('When', {
            'fields': ['timestamp']
        }),
        ('Context', {
            'fields': ['message', 'user_agent_display', 'extra_data_display']
        }),
    ]

    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        """Audit logs should not be manually added"""
        return False

    def has_change_permission(self, request, obj=None):
        """Audit logs should not be changed"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit logs"""
        return request.user.is_superuser

    def username_display(self, obj):
        """Display username with link to user"""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.username)
        return obj.username
    username_display.short_description = 'User'

    def action_badge(self, obj):
        """Display action as colored badge"""
        colors = {
            'CREATE': '#28a745',
            'UPDATE': '#007bff',
            'DELETE': '#dc3545',
            'VIEW': '#6c757d',
            'LOGIN': '#17a2b8',
            'LOGOUT': '#ffc107',
            'APPROVE': '#28a745',
            'REJECT': '#dc3545',
            'EXPORT': '#6f42c1',
            'IMPORT': '#e83e8c',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'

    def message_preview(self, obj):
        """Display truncated message"""
        if obj.message:
            return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
        return '-'
    message_preview.short_description = 'Message'

    def old_value_display(self, obj):
        """Display old value with formatting"""
        if not obj.old_value:
            return '-'
        return format_html('<pre style="margin: 0;">{}</pre>', obj.old_value[:500])
    old_value_display.short_description = 'Old Value'

    def new_value_display(self, obj):
        """Display new value with formatting"""
        if not obj.new_value:
            return '-'
        return format_html('<pre style="margin: 0;">{}</pre>', obj.new_value[:500])
    new_value_display.short_description = 'New Value'

    def user_agent_display(self, obj):
        """Display user agent with formatting"""
        if not obj.user_agent:
            return '-'
        return format_html('<pre style="margin: 0; white-space: pre-wrap;">{}</pre>', obj.user_agent)
    user_agent_display.short_description = 'User Agent'

    def extra_data_display(self, obj):
        """Display extra data as formatted JSON"""
        if not obj.extra_data:
            return '-'
        import json
        formatted = json.dumps(obj.extra_data, indent=2)
        return format_html('<pre style="margin: 0;">{}</pre>', formatted)
    extra_data_display.short_description = 'Extra Data'


@admin.register(ChangeHistory)
class ChangeHistoryAdmin(admin.ModelAdmin):
    """Admin interface for ChangeHistory"""

    list_display = [
        'changed_at',
        'content_type',
        'object_id',
        'changed_by',
        'changes_summary',
        'ip_address',
    ]

    list_filter = [
        'content_type',
        'changed_at',
        ('changed_by', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'object_id',
        'change_summary',
        'change_reason',
    ]

    readonly_fields = [
        'content_type',
        'object_id',
        'field_changes_display',
        'change_summary',
        'changed_by',
        'changed_at',
        'change_reason',
        'ip_address',
    ]

    fieldsets = [
        ('Object', {
            'fields': ['content_type', 'object_id']
        }),
        ('Changes', {
            'fields': ['field_changes_display', 'change_summary', 'change_reason']
        }),
        ('Metadata', {
            'fields': ['changed_by', 'changed_at', 'ip_address']
        }),
    ]

    date_hierarchy = 'changed_at'

    def has_add_permission(self, request):
        """Change history should not be manually added"""
        return False

    def has_change_permission(self, request, obj=None):
        """Change history should not be changed"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete change history"""
        return request.user.is_superuser

    def changes_summary(self, obj):
        """Display changes summary"""
        return obj.get_changes_display()[:100]
    changes_summary.short_description = 'Changes'

    def field_changes_display(self, obj):
        """Display field changes as formatted JSON"""
        import json
        formatted = json.dumps(obj.field_changes, indent=2)
        return format_html('<pre style="margin: 0;">{}</pre>', formatted)
    field_changes_display.short_description = 'Field Changes'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin interface for ActivityLog"""

    list_display = [
        'timestamp',
        'user',
        'activity_type_badge',
        'path',
        'duration_display',
        'ip_address',
    ]

    list_filter = [
        'activity_type',
        'timestamp',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'user__username',
        'path',
        'description',
    ]

    readonly_fields = [
        'user',
        'activity_type',
        'path',
        'query_params_display',
        'description',
        'timestamp',
        'duration_ms',
        'ip_address',
        'user_agent_display',
        'session_key',
        'metadata_display',
    ]

    fieldsets = [
        ('Activity', {
            'fields': ['user', 'activity_type', 'path', 'description']
        }),
        ('Timing', {
            'fields': ['timestamp', 'duration_ms']
        }),
        ('Details', {
            'fields': ['query_params_display', 'metadata_display']
        }),
        ('Context', {
            'fields': ['ip_address', 'user_agent_display', 'session_key']
        }),
    ]

    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        """Activity logs should not be manually added"""
        return False

    def has_change_permission(self, request, obj=None):
        """Activity logs should not be changed"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete activity logs"""
        return request.user.is_superuser

    def activity_type_badge(self, obj):
        """Display activity type as colored badge"""
        colors = {
            'PAGE_VIEW': '#007bff',
            'SEARCH': '#17a2b8',
            'FILTER': '#ffc107',
            'DOWNLOAD': '#28a745',
            'UPLOAD': '#e83e8c',
            'API_CALL': '#6f42c1',
            'REPORT': '#fd7e14',
            'PRINT': '#6c757d',
        }
        color = colors.get(obj.activity_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_activity_type_display()
        )
    activity_type_badge.short_description = 'Activity Type'

    def duration_display(self, obj):
        """Display duration with color coding"""
        if not obj.duration_ms:
            return '-'

        # Color code based on duration
        if obj.duration_ms < 500:
            color = '#28a745'  # Green
        elif obj.duration_ms < 1000:
            color = '#ffc107'  # Yellow
        else:
            color = '#dc3545'  # Red

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}ms</span>',
            color,
            obj.duration_ms
        )
    duration_display.short_description = 'Duration'

    def query_params_display(self, obj):
        """Display query params as formatted JSON"""
        if not obj.query_params:
            return '-'
        import json
        formatted = json.dumps(obj.query_params, indent=2)
        return format_html('<pre style="margin: 0;">{}</pre>', formatted)
    query_params_display.short_description = 'Query Parameters'

    def metadata_display(self, obj):
        """Display metadata as formatted JSON"""
        if not obj.metadata:
            return '-'
        import json
        formatted = json.dumps(obj.metadata, indent=2)
        return format_html('<pre style="margin: 0;">{}</pre>', formatted)
    metadata_display.short_description = 'Metadata'

    def user_agent_display(self, obj):
        """Display user agent with formatting"""
        if not obj.user_agent:
            return '-'
        return format_html('<pre style="margin: 0; white-space: pre-wrap;">{}</pre>', obj.user_agent)
    user_agent_display.short_description = 'User Agent'


@admin.register(SystemEvent)
class SystemEventAdmin(admin.ModelAdmin):
    """Admin interface for SystemEvent"""

    list_display = [
        'timestamp',
        'level_badge',
        'category_badge',
        'event_name',
        'user',
        'is_resolved',
        'message_preview',
    ]

    list_filter = [
        'level',
        'category',
        'is_resolved',
        'timestamp',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = [
        'event_name',
        'message',
        'exception_type',
        'exception_message',
    ]

    readonly_fields = [
        'level',
        'category',
        'event_name',
        'message',
        'exception_type',
        'exception_message',
        'stack_trace_display',
        'timestamp',
        'user',
        'request_path',
        'request_method',
        'ip_address',
        'extra_data_display',
    ]

    fieldsets = [
        ('Event', {
            'fields': ['level', 'category', 'event_name', 'message', 'timestamp']
        }),
        ('Exception Details', {
            'fields': ['exception_type', 'exception_message', 'stack_trace_display'],
            'classes': ['collapse']
        }),
        ('Request Context', {
            'fields': ['user', 'request_path', 'request_method', 'ip_address']
        }),
        ('Resolution', {
            'fields': ['is_resolved', 'resolved_at', 'resolved_by', 'resolution_notes']
        }),
        ('Additional Data', {
            'fields': ['extra_data_display'],
            'classes': ['collapse']
        }),
    ]

    date_hierarchy = 'timestamp'

    actions = ['mark_as_resolved']

    def has_add_permission(self, request):
        """System events should not be manually added"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete system events"""
        return request.user.is_superuser

    def level_badge(self, obj):
        """Display level as colored badge"""
        colors = {
            'DEBUG': '#6c757d',
            'INFO': '#17a2b8',
            'WARNING': '#ffc107',
            'ERROR': '#dc3545',
            'CRITICAL': '#8B0000',
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.level
        )
    level_badge.short_description = 'Level'

    def category_badge(self, obj):
        """Display category as colored badge"""
        colors = {
            'SYSTEM': '#007bff',
            'SECURITY': '#dc3545',
            'DATABASE': '#28a745',
            'EMAIL': '#17a2b8',
            'API': '#6f42c1',
            'TASK': '#fd7e14',
            'INTEGRATION': '#e83e8c',
        }
        color = colors.get(obj.category, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Category'

    def message_preview(self, obj):
        """Display truncated message"""
        return obj.message[:75] + '...' if len(obj.message) > 75 else obj.message
    message_preview.short_description = 'Message'

    def stack_trace_display(self, obj):
        """Display stack trace with formatting"""
        if not obj.stack_trace:
            return '-'
        return format_html('<pre style="margin: 0; white-space: pre-wrap;">{}</pre>', obj.stack_trace)
    stack_trace_display.short_description = 'Stack Trace'

    def extra_data_display(self, obj):
        """Display extra data as formatted JSON"""
        if not obj.extra_data:
            return '-'
        import json
        formatted = json.dumps(obj.extra_data, indent=2)
        return format_html('<pre style="margin: 0;">{}</pre>', formatted)
    extra_data_display.short_description = 'Extra Data'

    @admin.action(description='Mark selected events as resolved')
    def mark_as_resolved(self, request, queryset):
        """Bulk action to mark events as resolved"""
        from django.utils import timezone
        count = queryset.update(
            is_resolved=True,
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(request, f'{count} event(s) marked as resolved.')
