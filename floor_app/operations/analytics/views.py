"""
Analytics Views - Dashboards, Reports, and Visualizations
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from datetime import timedelta, datetime
import json

from .models import (
    UserSession, PageView, UserActivity, ModuleUsage,
    SystemMetric, ErrorLog, SearchQuery, DailyStatistics
)
from .utils import (
    calculate_active_users, get_top_users_by_activity,
    get_popular_pages, get_module_usage_stats,
    get_error_summary, get_search_insights,
    generate_user_activity_report
)


def staff_required(user):
    """Check if user is staff"""
    return user.is_staff


class AnalyticsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Main analytics dashboard"""
    template_name = 'analytics/dashboard.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Time ranges
        now = timezone.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)

        # Current active users (last 24 hours)
        context['active_users_24h'] = calculate_active_users(hours=24)
        context['active_users_1h'] = calculate_active_users(hours=1)

        # Today's statistics
        today_stats = DailyStatistics.objects.filter(date=today).first()
        if not today_stats:
            # Generate if not exists
            today_stats = DailyStatistics.generate_for_date(today)

        context['today_stats'] = today_stats

        # Yesterday's statistics for comparison
        yesterday_stats = DailyStatistics.objects.filter(date=yesterday).first()
        context['yesterday_stats'] = yesterday_stats

        # Calculate percentage changes
        if yesterday_stats and today_stats:
            context['logins_change'] = self.calculate_percentage_change(
                today_stats.total_logins, yesterday_stats.total_logins
            )
            context['page_views_change'] = self.calculate_percentage_change(
                today_stats.total_page_views, yesterday_stats.total_page_views
            )
            context['active_users_change'] = self.calculate_percentage_change(
                today_stats.active_users, yesterday_stats.active_users
            )

        # Last 7 days activity
        last_7_days_sessions = UserSession.objects.filter(login_time__gte=last_7_days)
        context['total_sessions_7d'] = last_7_days_sessions.count()
        context['avg_session_duration_7d'] = last_7_days_sessions.filter(
            duration_seconds__isnull=False
        ).aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0

        # Page views last 7 days
        context['total_page_views_7d'] = PageView.objects.filter(
            timestamp__gte=last_7_days
        ).count()

        # Activities last 7 days
        context['total_activities_7d'] = UserActivity.objects.filter(
            timestamp__gte=last_7_days
        ).count()

        # Top users by activity (last 30 days)
        context['top_users'] = get_top_users_by_activity(days=30, limit=10)

        # Popular pages (last 30 days)
        context['popular_pages'] = get_popular_pages(days=30, limit=10)

        # Module usage statistics (last 30 days)
        context['module_usage'] = get_module_usage_stats(days=30)

        # Error summary (last 7 days)
        context['error_summary'] = get_error_summary(days=7)

        # Recent errors
        context['recent_errors'] = ErrorLog.objects.filter(
            timestamp__gte=last_7_days,
            is_resolved=False
        ).order_by('-timestamp')[:10]

        # Chart data for last 7 days
        context['chart_data'] = self.get_chart_data_7_days()

        # Device breakdown (last 30 days)
        device_stats = UserSession.objects.filter(
            login_time__gte=last_30_days
        ).values('device_type').annotate(count=Count('id')).order_by('-count')
        context['device_stats'] = device_stats

        # Browser breakdown (last 30 days)
        browser_stats = UserSession.objects.filter(
            login_time__gte=last_30_days
        ).values('browser').annotate(count=Count('id')).order_by('-count')[:5]
        context['browser_stats'] = browser_stats

        return context

    def calculate_percentage_change(self, current, previous):
        """Calculate percentage change between two values"""
        if not previous or previous == 0:
            return 0
        return round(((current - previous) / previous) * 100, 1)

    def get_chart_data_7_days(self):
        """Get chart data for the last 7 days"""
        today = timezone.now().date()
        dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

        chart_data = {
            'labels': [d.strftime('%b %d') for d in dates],
            'logins': [],
            'page_views': [],
            'activities': [],
        }

        for date in dates:
            stats = DailyStatistics.objects.filter(date=date).first()
            chart_data['logins'].append(stats.total_logins if stats else 0)
            chart_data['page_views'].append(stats.total_page_views if stats else 0)
            chart_data['activities'].append(stats.total_actions if stats else 0)

        return chart_data


class UserActivityListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all user activities with filtering"""
    model = UserActivity
    template_name = 'analytics/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = UserActivity.objects.select_related('user', 'session').all()

        # Filtering
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        action_type = self.request.GET.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)

        module = self.request.GET.get('module')
        if module:
            queryset = queryset.filter(module=module)

        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(is_active=True).order_by('username')
        context['action_types'] = UserActivity.ACTION_TYPES
        context['modules'] = PageView.objects.values_list('module', flat=True).distinct().order_by('module')
        return context


class UserSessionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all user sessions"""
    model = UserSession
    template_name = 'analytics/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = UserSession.objects.select_related('user').all()

        # Filtering
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        device_type = self.request.GET.get('device_type')
        if device_type:
            queryset = queryset.filter(device_type=device_type)

        return queryset.order_by('-login_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(is_active=True).order_by('username')
        context['device_types'] = UserSession.objects.values_list('device_type', flat=True).distinct()
        return context


class UserSessionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detailed view of a specific session"""
    model = UserSession
    template_name = 'analytics/session_detail.html'
    context_object_name = 'session'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.object

        # Get page views for this session
        context['page_views'] = session.page_views.all().order_by('timestamp')

        # Get activities for this session
        context['activities'] = session.activities.all().order_by('timestamp')

        # Get errors for this session
        context['errors'] = session.errors.all().order_by('timestamp')

        # Calculate statistics
        page_views = session.page_views.all()
        context['total_page_views'] = page_views.count()
        context['unique_pages'] = page_views.values('url').distinct().count()
        context['avg_load_time'] = page_views.filter(
            load_time_ms__isnull=False
        ).aggregate(Avg('load_time_ms'))['load_time_ms__avg']

        return context


class ErrorLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all error logs"""
    model = ErrorLog
    template_name = 'analytics/error_list.html'
    context_object_name = 'errors'
    paginate_by = 50

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = ErrorLog.objects.select_related('user', 'session').all()

        # Filtering
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        module = self.request.GET.get('module')
        if module:
            queryset = queryset.filter(module=module)

        is_resolved = self.request.GET.get('is_resolved')
        if is_resolved == 'true':
            queryset = queryset.filter(is_resolved=True)
        elif is_resolved == 'false':
            queryset = queryset.filter(is_resolved=False)

        error_type = self.request.GET.get('error_type')
        if error_type:
            queryset = queryset.filter(error_type__icontains=error_type)

        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['severity_levels'] = ErrorLog.SEVERITY_LEVELS
        context['modules'] = ErrorLog.objects.values_list('module', flat=True).distinct().order_by('module')
        context['error_types'] = ErrorLog.objects.values_list('error_type', flat=True).distinct().order_by('error_type')[:20]
        return context


class ErrorLogDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detailed view of a specific error"""
    model = ErrorLog
    template_name = 'analytics/error_detail.html'
    context_object_name = 'error'

    def test_func(self):
        return self.request.user.is_staff


class ModuleUsageView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Module usage statistics and trends"""
    template_name = 'analytics/module_usage.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get date range from request or default to last 30 days
        days = int(self.request.GET.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)

        # Get module usage data
        module_usage = ModuleUsage.objects.filter(
            date__gte=start_date
        ).order_by('module', 'date')

        # Aggregate by module
        module_totals = module_usage.values('module').annotate(
            total_views=Sum('page_views'),
            total_users=Sum('unique_users'),
            total_actions=Sum('total_actions'),
            avg_load_time=Avg('avg_load_time_ms')
        ).order_by('-total_views')

        context['module_totals'] = module_totals
        context['days'] = days

        # Chart data for module trends
        context['chart_data'] = self.get_module_trend_chart_data(start_date)

        return context

    def get_module_trend_chart_data(self, start_date):
        """Get chart data for module trends"""
        module_usage = ModuleUsage.objects.filter(
            date__gte=start_date
        ).order_by('date', 'module')

        # Get unique modules
        modules = list(ModuleUsage.objects.filter(
            date__gte=start_date
        ).values_list('module', flat=True).distinct())

        # Get dates
        dates = []
        current_date = start_date
        end_date = timezone.now().date()
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)

        # Build chart data
        chart_data = {
            'labels': [d.strftime('%b %d') for d in dates],
            'datasets': {}
        }

        for module in modules:
            module_data = []
            for date in dates:
                usage = ModuleUsage.objects.filter(module=module, date=date).first()
                module_data.append(usage.page_views if usage else 0)
            chart_data['datasets'][module] = module_data

        return chart_data


class UserReportView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detailed activity report for a specific user"""
    model = User
    template_name = 'analytics/user_report.html'
    context_object_name = 'report_user'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get date range
        days = int(self.request.GET.get('days', 30))

        # Generate report
        report = generate_user_activity_report(self.object, days=days)
        context.update(report)

        # Recent activities
        cutoff_date = timezone.now() - timedelta(days=days)
        context['recent_activities'] = UserActivity.objects.filter(
            user=self.object,
            timestamp__gte=cutoff_date
        ).order_by('-timestamp')[:50]

        # Recent sessions
        context['recent_sessions'] = UserSession.objects.filter(
            user=self.object,
            login_time__gte=cutoff_date
        ).order_by('-login_time')[:20]

        return context


# API endpoints for AJAX requests

@login_required
@user_passes_test(staff_required)
def api_realtime_stats(request):
    """API endpoint for real-time statistics"""
    now = timezone.now()
    last_hour = now - timedelta(hours=1)
    last_5_min = now - timedelta(minutes=5)

    data = {
        'active_users_1h': calculate_active_users(hours=1),
        'active_users_5m': UserSession.objects.filter(
            last_activity__gte=last_5_min,
            is_active=True
        ).count(),
        'page_views_1h': PageView.objects.filter(timestamp__gte=last_hour).count(),
        'activities_1h': UserActivity.objects.filter(timestamp__gte=last_hour).count(),
        'errors_1h': ErrorLog.objects.filter(timestamp__gte=last_hour).count(),
        'timestamp': now.isoformat()
    }

    return JsonResponse(data)


@login_required
@user_passes_test(staff_required)
def api_module_stats(request):
    """API endpoint for module statistics"""
    days = int(request.GET.get('days', 7))
    module_usage = get_module_usage_stats(days=days)

    return JsonResponse({'module_usage': module_usage})


@login_required
@user_passes_test(staff_required)
def api_user_activity_timeline(request, user_id):
    """API endpoint for user activity timeline"""
    days = int(request.GET.get('days', 30))
    cutoff_date = timezone.now() - timedelta(days=days)

    user = get_object_or_404(User, id=user_id)
    activities = UserActivity.objects.filter(
        user=user,
        timestamp__gte=cutoff_date
    ).values('timestamp', 'action_type', 'module', 'description').order_by('timestamp')

    timeline_data = list(activities)

    return JsonResponse({'timeline': timeline_data}, safe=False)


@login_required
@user_passes_test(staff_required)
def export_analytics_report(request):
    """Export analytics data to CSV"""
    import csv
    from django.utils.timezone import now

    # Get parameters
    report_type = request.GET.get('type', 'activities')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="analytics_{report_type}_{now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)

    if report_type == 'activities':
        # Export user activities
        writer.writerow(['Timestamp', 'User', 'Action Type', 'Module', 'Description', 'Success'])

        queryset = UserActivity.objects.all()
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        for activity in queryset.select_related('user')[:10000]:  # Limit to 10k rows
            writer.writerow([
                activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                activity.user.username,
                activity.get_action_type_display(),
                activity.module,
                activity.description,
                'Yes' if activity.success else 'No'
            ])

    elif report_type == 'sessions':
        # Export sessions
        writer.writerow(['Login Time', 'Logout Time', 'User', 'Duration', 'Device', 'Browser', 'IP Address'])

        queryset = UserSession.objects.all()
        if date_from:
            queryset = queryset.filter(login_time__gte=date_from)
        if date_to:
            queryset = queryset.filter(login_time__lte=date_to)

        for session in queryset.select_related('user')[:10000]:
            writer.writerow([
                session.login_time.strftime('%Y-%m-%d %H:%M:%S'),
                session.logout_time.strftime('%Y-%m-%d %H:%M:%S') if session.logout_time else 'Active',
                session.user.username,
                session.get_duration_display(),
                session.device_type,
                session.browser,
                session.ip_address
            ])

    elif report_type == 'errors':
        # Export errors
        writer.writerow(['Timestamp', 'Severity', 'Error Type', 'Module', 'User', 'Message', 'Resolved'])

        queryset = ErrorLog.objects.all()
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        for error in queryset.select_related('user')[:10000]:
            writer.writerow([
                error.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                error.get_severity_display(),
                error.error_type,
                error.module,
                error.user.username if error.user else 'Anonymous',
                error.error_message[:200],
                'Yes' if error.is_resolved else 'No'
            ])

    return response
