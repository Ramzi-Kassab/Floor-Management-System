"""
Django Admin Configuration for Retrieval System
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import RetrievalRequest, RetrievalMetric


@admin.register(RetrievalRequest)
class RetrievalRequestAdmin(admin.ModelAdmin):
    """
    Admin interface for Retrieval Requests.
    """

    list_display = [
        'id',
        'employee_display',
        'supervisor_display',
        'object_type',
        'action_type',
        'status_badge',
        'submitted_at',
        'time_elapsed_display',
        'has_dependent_processes'
    ]

    list_filter = [
        'status',
        'action_type',
        'has_dependent_processes',
        'submitted_at',
        'approved_at'
    ]

    search_fields = [
        'employee__username',
        'employee__first_name',
        'employee__last_name',
        'supervisor__username',
        'supervisor__first_name',
        'supervisor__last_name',
        'reason',
        'object_id'
    ]

    readonly_fields = [
        'employee',
        'supervisor',
        'content_type',
        'object_id',
        'original_data',
        'submitted_at',
        'approved_at',
        'completed_at',
        'rejected_at',
        'time_elapsed',
        'supervisor_notified_at',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Request Information', {
            'fields': (
                'employee',
                'supervisor',
                'action_type',
                'reason',
                'status'
            )
        }),
        ('Object Information', {
            'fields': (
                'content_type',
                'object_id',
                'original_data'
            )
        }),
        ('Dependencies', {
            'fields': (
                'has_dependent_processes',
                'dependent_process_details'
            )
        }),
        ('Timing', {
            'fields': (
                'submitted_at',
                'time_elapsed',
                'approved_at',
                'completed_at'
            )
        }),
        ('Notifications', {
            'fields': (
                'notification_sent',
                'supervisor_notified_at'
            )
        }),
        ('Rejection Details', {
            'fields': (
                'rejected_by',
                'rejected_at',
                'rejection_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': (
                'created_at',
                'created_by',
                'updated_at',
                'updated_by'
            ),
            'classes': ('collapse',)
        })
    )

    def employee_display(self, obj):
        """Display employee with link."""
        if obj.employee:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.employee.id,
                obj.employee.get_full_name() or obj.employee.username
            )
        return '-'
    employee_display.short_description = 'Employee'

    def supervisor_display(self, obj):
        """Display supervisor with link."""
        if obj.supervisor:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.supervisor.id,
                obj.supervisor.get_full_name() or obj.supervisor.username
            )
        return '-'
    supervisor_display.short_description = 'Supervisor'

    def object_type(self, obj):
        """Display object type."""
        return obj.content_type.model if obj.content_type else '-'
    object_type.short_description = 'Object Type'

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'PENDING': '#ffc107',
            'AUTO_APPROVED': '#28a745',
            'APPROVED': '#28a745',
            'REJECTED': '#dc3545',
            'COMPLETED': '#007bff',
            'CANCELLED': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def time_elapsed_display(self, obj):
        """Display time elapsed with color coding."""
        if obj.time_elapsed:
            minutes = obj.time_elapsed.total_seconds() / 60
            color = '#28a745' if minutes <= 15 else '#dc3545'
            return format_html(
                '<span style="color: {};">{:.0f} min</span>',
                color,
                minutes
            )
        return '-'
    time_elapsed_display.short_description = 'Time Elapsed'

    def has_permissions_to_change(self, request, obj=None):
        """Limit change permissions."""
        return request.user.is_superuser

    def has_add_permission(self, request):
        """Disable add in admin (should be created through views)."""
        return False


@admin.register(RetrievalMetric)
class RetrievalMetricAdmin(admin.ModelAdmin):
    """
    Admin interface for Retrieval Metrics.
    """

    list_display = [
        'employee_display',
        'period_type',
        'period_range',
        'accuracy_display',
        'total_actions',
        'retrieval_requests',
        'calculated_at'
    ]

    list_filter = [
        'period_type',
        'period_start',
        'period_end'
    ]

    search_fields = [
        'employee__username',
        'employee__first_name',
        'employee__last_name'
    ]

    readonly_fields = [
        'employee',
        'period_type',
        'period_start',
        'period_end',
        'total_actions',
        'retrieval_requests',
        'auto_approved',
        'manually_approved',
        'rejected',
        'completed',
        'accuracy_rate',
        'average_time_to_request',
        'calculated_at',
        'updated_at'
    ]

    def employee_display(self, obj):
        """Display employee with link."""
        if obj.employee:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.employee.id,
                obj.employee.get_full_name() or obj.employee.username
            )
        return '-'
    employee_display.short_description = 'Employee'

    def period_range(self, obj):
        """Display period range."""
        return f"{obj.period_start} to {obj.period_end}"
    period_range.short_description = 'Period'

    def accuracy_display(self, obj):
        """Display accuracy with color coding."""
        rate = float(obj.accuracy_rate)
        if rate >= 95:
            color = '#28a745'
        elif rate >= 90:
            color = '#ffc107'
        else:
            color = '#dc3545'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}%</span>',
            color,
            rate
        )
    accuracy_display.short_description = 'Accuracy'

    def has_add_permission(self, request):
        """Disable add in admin (calculated automatically)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete metrics."""
        return request.user.is_superuser
