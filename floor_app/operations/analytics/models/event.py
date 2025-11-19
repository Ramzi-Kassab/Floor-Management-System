"""
App Usage Event Tracking Models

Tracks who uses what features, when, and how often.
Enables analytics on feature adoption, usage patterns, and user behavior.
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from floor_app.mixins import AuditMixin


class AppEvent(AuditMixin):
    """
    Generic event tracking for all app usage.

    Captures:
    - Page views
    - Report views
    - Actions (create, update, delete)
    - Exports
    - Custom events

    Used for:
    - Usage analytics (which pages are used most)
    - Feature adoption tracking
    - User behavior analysis
    - Email reduction measurement (report usage vs email requests)
    """

    EVENT_TYPE_CHOICES = (
        ('PAGE_VIEW', 'Page View'),
        ('REPORT_VIEW', 'Report View'),
        ('ACTION', 'Action'),
        ('EXPORT', 'Export'),
        ('SEARCH', 'Search'),
        ('FILTER', 'Filter'),
        ('CREATE', 'Create Record'),
        ('UPDATE', 'Update Record'),
        ('DELETE', 'Delete Record'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ERROR', 'Error'),
        ('API_CALL', 'API Call'),
        ('CUSTOM', 'Custom Event'),
    )

    # Who
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_events',
        db_index=True,
        help_text="User who triggered this event (null for anonymous)"
    )

    # What
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of event"
    )

    view_name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Logical view/feature name (e.g., 'job_card_detail', 'cutter_inventory_report')"
    )

    event_category = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="Category: Inventory, Production, Planning, Quality, HR, etc."
    )

    # Where (HTTP details)
    http_path = models.CharField(
        max_length=500,
        help_text="URL path"
    )

    http_method = models.CharField(
        max_length=10,
        default='GET',
        help_text="HTTP method (GET, POST, etc.)"
    )

    query_string = models.TextField(
        blank=True,
        default="",
        help_text="Query string parameters"
    )

    # When
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When event occurred"
    )

    # Performance
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Request duration in milliseconds"
    )

    # Client info
    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address"
    )

    user_agent = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="User agent string (truncated)"
    )

    # Related object (generic foreign key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type of related object"
    )

    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of related object"
    )

    related_object = GenericForeignKey('content_type', 'object_id')

    # Additional context
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Additional event context.
        Examples:
        - Search terms
        - Filter criteria
        - Export format
        - Error details
        - Custom event data
        """
    )

    # Session tracking
    session_key = models.CharField(
        max_length=100,
        blank=True,
        default="",
        db_index=True,
        help_text="Session key for grouping events"
    )

    class Meta:
        db_table = "analytics_app_event"
        verbose_name = "App Event"
        verbose_name_plural = "App Events"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp'], name='ix_event_user_time'),
            models.Index(fields=['event_type', 'timestamp'], name='ix_event_type_time'),
            models.Index(fields=['view_name', 'timestamp'], name='ix_event_view_time'),
            models.Index(fields=['event_category', 'timestamp'], name='ix_event_cat_time'),
            models.Index(fields=['timestamp'], name='ix_event_timestamp'),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} - {self.event_type} - {self.view_name} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def log_event(cls, user, event_type, view_name, request=None, **kwargs):
        """
        Convenient method to log an event.

        Usage:
            AppEvent.log_event(
                user=request.user,
                event_type='REPORT_VIEW',
                view_name='cutter_inventory_report',
                event_category='Inventory',
                related_object=some_model_instance,
                metadata={'filters': {'status': 'active'}}
            )
        """
        event_data = {
            'user': user if user and user.is_authenticated else None,
            'event_type': event_type,
            'view_name': view_name,
        }

        # Extract from request if provided
        if request:
            event_data.update({
                'http_path': request.path,
                'http_method': request.method,
                'query_string': request.META.get('QUERY_STRING', ''),
                'client_ip': cls._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'session_key': request.session.session_key if hasattr(request, 'session') else '',
            })

        # Override with explicit kwargs
        event_data.update(kwargs)

        # Handle related_object
        if 'related_object' in event_data:
            obj = event_data.pop('related_object')
            if obj:
                event_data['content_type'] = ContentType.objects.get_for_model(obj)
                event_data['object_id'] = obj.pk

        return cls.objects.create(**event_data)

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class EventSummary(models.Model):
    """
    Pre-aggregated event statistics for performance.

    Generated periodically (hourly/daily) to avoid slow queries on AppEvent table.
    """

    PERIOD_CHOICES = (
        ('HOUR', 'Hourly'),
        ('DAY', 'Daily'),
        ('WEEK', 'Weekly'),
        ('MONTH', 'Monthly'),
    )

    # Time period
    period_type = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        db_index=True
    )

    period_start = models.DateTimeField(
        db_index=True,
        help_text="Start of period"
    )

    period_end = models.DateTimeField(
        help_text="End of period"
    )

    # What was summarized
    event_type = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Event type (empty = all types)"
    )

    view_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="View name (empty = all views)"
    )

    event_category = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Category (empty = all categories)"
    )

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User (null = all users)"
    )

    # Aggregated metrics
    event_count = models.IntegerField(
        default=0,
        help_text="Number of events in this period"
    )

    unique_users = models.IntegerField(
        default=0,
        help_text="Number of unique users"
    )

    avg_duration_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="Average request duration"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_event_summary"
        verbose_name = "Event Summary"
        verbose_name_plural = "Event Summaries"
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['period_type', 'period_start'], name='ix_summary_period'),
            models.Index(fields=['view_name', 'period_start'], name='ix_summary_view'),
            models.Index(fields=['event_category', 'period_start'], name='ix_summary_cat'),
        ]
        unique_together = [
            ['period_type', 'period_start', 'event_type', 'view_name', 'event_category', 'user']
        ]

    def __str__(self):
        return f"{self.period_type} {self.period_start.strftime('%Y-%m-%d')} - {self.view_name or 'ALL'} ({self.event_count} events)"

    @classmethod
    def generate_summary(cls, period_type, start_time, end_time):
        """
        Generate summary for a time period.
        Called from scheduled task.
        """
        from django.db.models import Count, Avg

        # Get events in period
        events = AppEvent.objects.filter(
            timestamp__gte=start_time,
            timestamp__lt=end_time
        )

        # Overall summary
        overall = events.aggregate(
            count=Count('id'),
            unique_users=Count('user', distinct=True),
            avg_duration=Avg('duration_ms')
        )

        cls.objects.update_or_create(
            period_type=period_type,
            period_start=start_time,
            period_end=end_time,
            event_type='',
            view_name='',
            event_category='',
            user=None,
            defaults={
                'event_count': overall['count'] or 0,
                'unique_users': overall['unique_users'] or 0,
                'avg_duration_ms': overall['avg_duration'],
            }
        )

        # By view name
        view_summaries = events.values('view_name').annotate(
            count=Count('id'),
            unique_users=Count('user', distinct=True),
            avg_duration=Avg('duration_ms')
        )

        for summary in view_summaries:
            cls.objects.update_or_create(
                period_type=period_type,
                period_start=start_time,
                period_end=end_time,
                event_type='',
                view_name=summary['view_name'],
                event_category='',
                user=None,
                defaults={
                    'event_count': summary['count'],
                    'unique_users': summary['unique_users'],
                    'avg_duration_ms': summary['avg_duration'],
                }
            )

        # By category
        cat_summaries = events.values('event_category').annotate(
            count=Count('id'),
            unique_users=Count('user', distinct=True),
            avg_duration=Avg('duration_ms')
        )

        for summary in cat_summaries:
            if summary['event_category']:
                cls.objects.update_or_create(
                    period_type=period_type,
                    period_start=start_time,
                    period_end=end_time,
                    event_type='',
                    view_name='',
                    event_category=summary['event_category'],
                    user=None,
                    defaults={
                        'event_count': summary['count'],
                        'unique_users': summary['unique_users'],
                        'avg_duration_ms': summary['avg_duration'],
                    }
                )
