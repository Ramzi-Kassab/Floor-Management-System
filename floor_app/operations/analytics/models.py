"""
Analytics and Activity Monitoring Models
Comprehensive tracking of user activities, system usage, and performance metrics
"""
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from datetime import timedelta
import json


class UserSession(models.Model):
    """Track user login sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_sessions')
    session_key = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # Desktop, Mobile, Tablet
    browser = models.CharField(max_length=50, blank=True)
    operating_system = models.CharField(max_length=50, blank=True)

    login_time = models.DateTimeField(auto_now_add=True, db_index=True)
    last_activity = models.DateTimeField(auto_now=True, db_index=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    # Location data (optional)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'analytics_user_session'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['is_active', '-last_activity']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M')}"

    def calculate_duration(self):
        """Calculate session duration"""
        if self.logout_time:
            self.duration_seconds = int((self.logout_time - self.login_time).total_seconds())
        elif self.last_activity:
            self.duration_seconds = int((self.last_activity - self.login_time).total_seconds())
        self.save(update_fields=['duration_seconds'])
        return self.duration_seconds

    def get_duration_display(self):
        """Get human-readable duration"""
        if not self.duration_seconds:
            return "N/A"
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"


class PageView(models.Model):
    """Track page views and navigation patterns"""
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='page_views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='page_views')

    url = models.CharField(max_length=500, db_index=True)
    url_name = models.CharField(max_length=100, blank=True, db_index=True)  # URL name from urls.py
    module = models.CharField(max_length=50, blank=True, db_index=True)  # hr, inventory, production, etc.
    view_name = models.CharField(max_length=100, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    referrer = models.CharField(max_length=500, blank=True)

    # Performance metrics
    load_time_ms = models.IntegerField(null=True, blank=True, help_text="Page load time in milliseconds")

    # Query parameters (stored as JSON)
    query_params = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'analytics_page_view'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['module', '-timestamp']),
            models.Index(fields=['url_name', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.url} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class UserActivity(models.Model):
    """Track specific user actions and events"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('search', 'Search'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('submit', 'Submit'),
        ('download', 'Download'),
        ('upload', 'Upload'),
        ('print', 'Print'),
        ('other', 'Other'),
    ]

    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')

    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, db_index=True)
    module = models.CharField(max_length=50, blank=True, db_index=True)
    description = models.CharField(max_length=500)

    # Generic relation to track which object was affected
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Additional context (stored as JSON)
    metadata = models.JSONField(default=dict, blank=True)

    # Success/failure tracking
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'analytics_user_activity'
        ordering = ['-timestamp']
        verbose_name_plural = 'User Activities'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['module', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.description}"


class ModuleUsage(models.Model):
    """Aggregate module usage statistics (daily)"""
    module = models.CharField(max_length=50, db_index=True)
    date = models.DateField(db_index=True)

    # Counts
    page_views = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    total_actions = models.IntegerField(default=0)

    # Action breakdown
    creates = models.IntegerField(default=0)
    reads = models.IntegerField(default=0)
    updates = models.IntegerField(default=0)
    deletes = models.IntegerField(default=0)

    # Performance
    avg_load_time_ms = models.FloatField(null=True, blank=True)

    # Time spent
    total_time_seconds = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_module_usage'
        ordering = ['-date', 'module']
        unique_together = [['module', 'date']]
        indexes = [
            models.Index(fields=['module', '-date']),
        ]

    def __str__(self):
        return f"{self.module} - {self.date}"


class SystemMetric(models.Model):
    """Track system-wide performance and health metrics"""
    METRIC_TYPES = [
        ('response_time', 'Response Time'),
        ('error_rate', 'Error Rate'),
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('disk_usage', 'Disk Usage'),
        ('database_queries', 'Database Queries'),
        ('active_users', 'Active Users'),
        ('concurrent_sessions', 'Concurrent Sessions'),
    ]

    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES, db_index=True)
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)  # ms, %, count, etc.

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Additional context
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'analytics_system_metric'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_type', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value} {self.unit}"


class ErrorLog(models.Model):
    """Track application errors and exceptions"""
    SEVERITY_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]

    session = models.ForeignKey(UserSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='errors')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='error_logs')

    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='error', db_index=True)
    error_type = models.CharField(max_length=100, db_index=True)  # Exception class name
    error_message = models.TextField()

    url = models.CharField(max_length=500, blank=True)
    module = models.CharField(max_length=50, blank=True, db_index=True)
    view_name = models.CharField(max_length=100, blank=True)

    # Stack trace
    traceback = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Context
    request_data = models.JSONField(default=dict, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_errors')
    resolution_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'analytics_error_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['module', '-timestamp']),
            models.Index(fields=['is_resolved', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.get_severity_display()}: {self.error_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class SearchQuery(models.Model):
    """Track search queries for analytics and optimization"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_queries')
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='searches', null=True, blank=True)

    module = models.CharField(max_length=50, blank=True, db_index=True)
    search_term = models.CharField(max_length=500, db_index=True)
    filters_applied = models.JSONField(default=dict, blank=True)

    results_count = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Did user click on results?
    clicked_result = models.BooleanField(default=False)

    class Meta:
        db_table = 'analytics_search_query'
        ordering = ['-timestamp']
        verbose_name_plural = 'Search Queries'
        indexes = [
            models.Index(fields=['module', '-timestamp']),
            models.Index(fields=['search_term']),
        ]

    def __str__(self):
        return f"{self.user.username} searched '{self.search_term}' in {self.module}"


class DailyStatistics(models.Model):
    """Aggregated daily statistics for quick reporting"""
    date = models.DateField(unique=True, db_index=True)

    # User metrics
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)

    # Activity metrics
    total_logins = models.IntegerField(default=0)
    total_page_views = models.IntegerField(default=0)
    total_actions = models.IntegerField(default=0)

    # Performance metrics
    avg_session_duration_seconds = models.FloatField(null=True, blank=True)
    avg_page_load_time_ms = models.FloatField(null=True, blank=True)

    # Error metrics
    total_errors = models.IntegerField(default=0)
    critical_errors = models.IntegerField(default=0)

    # Module breakdown (stored as JSON)
    module_statistics = models.JSONField(default=dict, blank=True)

    # Peak usage
    peak_concurrent_users = models.IntegerField(default=0)
    peak_hour = models.IntegerField(null=True, blank=True)  # 0-23

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_daily_statistics'
        ordering = ['-date']
        verbose_name_plural = 'Daily Statistics'

    def __str__(self):
        return f"Stats for {self.date}"

    @classmethod
    def generate_for_date(cls, date):
        """Generate/update statistics for a specific date"""
        from django.db.models import Count, Avg, Sum, Max
        from django.contrib.auth.models import User

        # Get or create daily stats
        stats, created = cls.objects.get_or_create(date=date)

        # User metrics
        stats.total_users = User.objects.filter(is_active=True).count()
        stats.active_users = UserSession.objects.filter(
            login_time__date=date
        ).values('user').distinct().count()
        stats.new_users = User.objects.filter(date_joined__date=date).count()

        # Activity metrics
        stats.total_logins = UserSession.objects.filter(login_time__date=date).count()
        stats.total_page_views = PageView.objects.filter(timestamp__date=date).count()
        stats.total_actions = UserActivity.objects.filter(timestamp__date=date).count()

        # Performance metrics
        avg_duration = UserSession.objects.filter(
            login_time__date=date,
            duration_seconds__isnull=False
        ).aggregate(Avg('duration_seconds'))['duration_seconds__avg']
        stats.avg_session_duration_seconds = avg_duration

        avg_load = PageView.objects.filter(
            timestamp__date=date,
            load_time_ms__isnull=False
        ).aggregate(Avg('load_time_ms'))['load_time_ms__avg']
        stats.avg_page_load_time_ms = avg_load

        # Error metrics
        stats.total_errors = ErrorLog.objects.filter(timestamp__date=date).count()
        stats.critical_errors = ErrorLog.objects.filter(
            timestamp__date=date,
            severity='critical'
        ).count()

        # Module statistics
        module_stats = {}
        for module_usage in ModuleUsage.objects.filter(date=date):
            module_stats[module_usage.module] = {
                'page_views': module_usage.page_views,
                'unique_users': module_usage.unique_users,
                'total_actions': module_usage.total_actions,
            }
        stats.module_statistics = module_stats

        stats.save()
        return stats
