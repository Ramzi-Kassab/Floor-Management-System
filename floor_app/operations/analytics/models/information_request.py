"""
Information Request Tracking Models

Tracks questions/requests that come via email, phone, WhatsApp, etc.
Measures the need for features and tracks email reduction over time.

Business Value:
- Identifies missing features (what people keep asking for)
- Measures ROI of new reports/dashboards (email reduction)
- Prioritizes development based on actual user needs
"""

from django.db import models
from django.utils import timezone
from floor_app.mixins import AuditMixin, SoftDeleteMixin


class InformationRequest(AuditMixin, SoftDeleteMixin):
    """
    Tracks information requests that come outside the system.

    Examples:
    - "Can you send me the status of bit SN12345?"
    - "What's the current stock of ENO reclaimed cutters?"
    - "Please share this week's production plan"
    - "When will job card 2025-ARDT-042 be ready?"

    Purpose:
    - Log what people ask for that's not in the system yet
    - Measure email reduction after adding features
    - Prioritize development based on request frequency
    """

    CHANNEL_CHOICES = (
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('PHONE', 'Phone Call'),
        ('VERBAL', 'Verbal / In Person'),
        ('TEAMS', 'Microsoft Teams'),
        ('SLACK', 'Slack'),
        ('OTHER', 'Other'),
    )

    CATEGORY_CHOICES = (
        ('STATUS', 'Status Inquiry'),
        ('REPORT', 'Report Request'),
        ('STOCK', 'Stock / Inventory Query'),
        ('PLANNING', 'Planning / Schedule'),
        ('QUALITY', 'Quality / Inspection'),
        ('FINANCE', 'Financial / Quotation'),
        ('TECHNICAL', 'Technical Specs / Details'),
        ('DOCUMENT', 'Document Request'),
        ('APPROVAL', 'Approval Request'),
        ('OTHER', 'Other'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open (Not Covered)'),
        ('COVERED', 'Covered by System'),
        ('IN_PROGRESS', 'Feature In Progress'),
        ('WONT_FIX', 'Won\'t Implement'),
        ('DUPLICATE', 'Duplicate Request'),
    )

    # Who asked
    requester = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='information_requests',
        help_text="User who made the request (if known)"
    )

    requester_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Name of requester (for external users)"
    )

    requester_email = models.EmailField(
        blank=True,
        default="",
        help_text="Email of requester"
    )

    requester_role = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Role/department of requester"
    )

    # How they asked
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        db_index=True,
        help_text="How the request came in"
    )

    # When
    request_datetime = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the request was made"
    )

    # What they asked
    summary = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Short summary of what was requested"
    )

    details = models.TextField(
        blank=True,
        default="",
        help_text="Full details of the request"
    )

    request_category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        db_index=True,
        help_text="Category of request"
    )

    # Related objects (nullable - not all requests relate to specific records)
    related_job_card = models.ForeignKey(
        'production.JobCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='information_requests',
        help_text="Related job card (if applicable)"
    )

    related_serial_unit = models.ForeignKey(
        'inventory.SerialUnit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='information_requests',
        help_text="Related serial unit (if applicable)"
    )

    related_customer = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Related customer name"
    )

    # Frequency tracking
    is_repeated = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Is this a repeated/recurring request?"
    )

    repeat_count = models.IntegerField(
        default=1,
        help_text="How many times this same request has been made"
    )

    similar_requests = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='similar_to',
        help_text="Link to similar/duplicate requests"
    )

    # System coverage
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN',
        db_index=True,
        help_text="Whether this is now covered by the system"
    )

    is_now_covered_by_system = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Quick flag: Is this now available in the web app?"
    )

    covered_by_view_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="View/page name that now covers this request"
    )

    covered_by_url = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="URL of page/report that answers this request"
    )

    covered_since = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this was marked as covered"
    )

    # Response tracking
    response_time_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="How long it took to respond (minutes)"
    )

    response_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes on how we responded"
    )

    # Priority
    priority = models.IntegerField(
        default=50,
        help_text="Priority score (higher = more important to implement)"
    )

    # Tags for categorization
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for flexible categorization"
    )

    class Meta:
        db_table = "analytics_information_request"
        verbose_name = "Information Request"
        verbose_name_plural = "Information Requests"
        ordering = ['-request_datetime']
        indexes = [
            models.Index(fields=['request_datetime'], name='ix_inforeq_date'),
            models.Index(fields=['status'], name='ix_inforeq_status'),
            models.Index(fields=['request_category'], name='ix_inforeq_cat'),
            models.Index(fields=['channel'], name='ix_inforeq_channel'),
            models.Index(fields=['is_repeated'], name='ix_inforeq_repeat'),
            models.Index(fields=['is_now_covered_by_system'], name='ix_inforeq_covered'),
        ]

    def __str__(self):
        return f"{self.summary[:50]} ({self.get_channel_display()}) - {self.request_datetime.strftime('%Y-%m-%d')}"

    def mark_as_covered(self, view_name, url='', user=None):
        """Mark this request as now covered by the system."""
        self.status = 'COVERED'
        self.is_now_covered_by_system = True
        self.covered_by_view_name = view_name
        self.covered_by_url = url
        self.covered_since = timezone.now()
        self.save()

        # Log event
        from .event import AppEvent
        if user:
            AppEvent.log_event(
                user=user,
                event_type='ACTION',
                view_name='information_request_marked_covered',
                event_category='Analytics',
                related_object=self,
                metadata={
                    'covered_by_view': view_name,
                    'request_category': self.request_category
                }
            )

    def increment_repeat_count(self):
        """Increment repeat count for recurring requests."""
        self.repeat_count += 1
        self.is_repeated = True
        self.save(update_fields=['repeat_count', 'is_repeated', 'updated_at'])

    @classmethod
    def get_top_uncovered_requests(cls, limit=10):
        """
        Get top repeated requests that are not yet covered.
        Used to prioritize development.
        """
        return cls.objects.filter(
            is_now_covered_by_system=False,
            status='OPEN'
        ).order_by('-repeat_count', '-priority')[:limit]

    @classmethod
    def get_email_reduction_stats(cls, start_date=None, end_date=None):
        """
        Calculate email reduction statistics.

        Returns dict with:
        - total_requests: Total requests in period
        - covered_requests: Requests now covered
        - open_requests: Requests still not covered
        - reduction_percentage: % of requests now covered
        - by_category: Breakdown by category
        """
        from django.db.models import Count, Q

        qs = cls.objects.all()
        if start_date:
            qs = qs.filter(request_datetime__gte=start_date)
        if end_date:
            qs = qs.filter(request_datetime__lte=end_date)

        total = qs.count()
        covered = qs.filter(is_now_covered_by_system=True).count()
        open_count = qs.filter(is_now_covered_by_system=False).count()

        reduction_pct = (covered / total * 100) if total > 0 else 0

        # By category
        by_category = list(qs.values('request_category').annotate(
            total=Count('id'),
            covered=Count('id', filter=Q(is_now_covered_by_system=True)),
            open=Count('id', filter=Q(is_now_covered_by_system=False))
        ))

        return {
            'total_requests': total,
            'covered_requests': covered,
            'open_requests': open_count,
            'reduction_percentage': round(reduction_pct, 1),
            'by_category': by_category,
        }


class RequestTrend(models.Model):
    """
    Pre-aggregated request trends for analytics.

    Generated periodically to show trends over time.
    """

    PERIOD_CHOICES = (
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
        db_index=True
    )

    period_end = models.DateTimeField()

    # Category
    request_category = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Category (empty = all)"
    )

    # Metrics
    total_requests = models.IntegerField(
        default=0,
        help_text="Total requests in period"
    )

    covered_requests = models.IntegerField(
        default=0,
        help_text="Requests marked as covered"
    )

    open_requests = models.IntegerField(
        default=0,
        help_text="Requests still open"
    )

    repeated_requests = models.IntegerField(
        default=0,
        help_text="Repeated requests"
    )

    avg_response_time_minutes = models.FloatField(
        null=True,
        blank=True,
        help_text="Average response time"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_request_trend"
        verbose_name = "Request Trend"
        verbose_name_plural = "Request Trends"
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['period_type', 'period_start'], name='ix_reqtrend_period'),
            models.Index(fields=['request_category', 'period_start'], name='ix_reqtrend_cat'),
        ]
        unique_together = [
            ['period_type', 'period_start', 'request_category']
        ]

    def __str__(self):
        cat_str = self.request_category or "ALL"
        return f"{self.period_type} {self.period_start.strftime('%Y-%m-%d')} - {cat_str} ({self.total_requests} requests)"

    @classmethod
    def generate_trend(cls, period_type, start_time, end_time):
        """Generate trend summary for period."""
        from django.db.models import Count, Avg, Q

        requests = InformationRequest.objects.filter(
            request_datetime__gte=start_time,
            request_datetime__lt=end_time
        )

        # Overall
        overall_stats = requests.aggregate(
            total=Count('id'),
            covered=Count('id', filter=Q(is_now_covered_by_system=True)),
            open=Count('id', filter=Q(is_now_covered_by_system=False)),
            repeated=Count('id', filter=Q(is_repeated=True)),
            avg_response=Avg('response_time_minutes')
        )

        cls.objects.update_or_create(
            period_type=period_type,
            period_start=start_time,
            period_end=end_time,
            request_category='',
            defaults={
                'total_requests': overall_stats['total'] or 0,
                'covered_requests': overall_stats['covered'] or 0,
                'open_requests': overall_stats['open'] or 0,
                'repeated_requests': overall_stats['repeated'] or 0,
                'avg_response_time_minutes': overall_stats['avg_response'],
            }
        )

        # By category
        category_stats = requests.values('request_category').annotate(
            total=Count('id'),
            covered=Count('id', filter=Q(is_now_covered_by_system=True)),
            open=Count('id', filter=Q(is_now_covered_by_system=False)),
            repeated=Count('id', filter=Q(is_repeated=True)),
            avg_response=Avg('response_time_minutes')
        )

        for stats in category_stats:
            cls.objects.update_or_create(
                period_type=period_type,
                period_start=start_time,
                period_end=end_time,
                request_category=stats['request_category'],
                defaults={
                    'total_requests': stats['total'],
                    'covered_requests': stats['covered'],
                    'open_requests': stats['open'],
                    'repeated_requests': stats['repeated'],
                    'avg_response_time_minutes': stats['avg_response'],
                }
            )
