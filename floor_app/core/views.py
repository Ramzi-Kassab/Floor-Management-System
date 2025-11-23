"""
Views for core system monitoring and administration

Provides:
- System health dashboard
- Activity reports
- Audit log viewers
- Export utilities
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta

from .models import AuditLog, ActivityLog, SystemEvent, ChangeHistory
from .utils import get_system_health_summary, get_user_activity_summary
from .exports import export_queryset_to_excel, export_queryset_to_pdf, export_queryset_to_csv


def is_staff_or_superuser(user):
    """Check if user is staff or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_staff_or_superuser)
def system_dashboard(request):
    """
    Main system monitoring dashboard

    URL: /core/dashboard/
    """
    # Get time range
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)

    # System health
    health = get_system_health_summary()

    # Activity statistics
    total_activities = ActivityLog.objects.filter(timestamp__gte=start_date).count()
    unique_users = ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).values('user').distinct().count()

    # Audit statistics
    total_audits = AuditLog.objects.filter(timestamp__gte=start_date).count()

    # Activities by type
    activities_by_type = ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Actions by type
    actions_by_type = AuditLog.objects.filter(
        timestamp__gte=start_date
    ).values('action').annotate(
        count=Count('id')
    ).order_by('-count')

    # Most active users
    top_users = ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Recent errors
    recent_errors = SystemEvent.objects.filter(
        level__in=['ERROR', 'CRITICAL'],
        timestamp__gte=start_date
    ).order_by('-timestamp')[:10]

    # System events by level
    events_by_level = SystemEvent.objects.filter(
        timestamp__gte=start_date
    ).values('level').annotate(
        count=Count('id')
    ).order_by('-count')

    # Average request duration
    avg_duration = ActivityLog.objects.filter(
        timestamp__gte=start_date,
        duration_ms__isnull=False
    ).aggregate(avg=Avg('duration_ms'))['avg']

    context = {
        'health': health,
        'days': days,
        'start_date': start_date,
        'total_activities': total_activities,
        'unique_users': unique_users,
        'total_audits': total_audits,
        'activities_by_type': activities_by_type,
        'actions_by_type': actions_by_type,
        'top_users': top_users,
        'recent_errors': recent_errors,
        'events_by_level': events_by_level,
        'avg_duration': avg_duration,
    }

    return render(request, 'core/dashboard.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def activity_logs(request):
    """
    Activity logs viewer

    URL: /core/activity-logs/
    """
    # Filters
    days = int(request.GET.get('days', 7))
    user_filter = request.GET.get('user')
    activity_type = request.GET.get('type')

    # Build queryset
    start_date = timezone.now() - timedelta(days=days)
    logs = ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).select_related('user').order_by('-timestamp')

    if user_filter:
        logs = logs.filter(user__username=user_filter)

    if activity_type:
        logs = logs.filter(activity_type=activity_type)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Activity types for filter
    activity_types = ActivityLog.ACTIVITY_TYPES

    context = {
        'page_obj': page_obj,
        'days': days,
        'user_filter': user_filter,
        'activity_type': activity_type,
        'activity_types': activity_types,
    }

    return render(request, 'core/activity_logs.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def audit_logs(request):
    """
    Audit logs viewer

    URL: /core/audit-logs/
    """
    # Filters
    days = int(request.GET.get('days', 7))
    user_filter = request.GET.get('user')
    action = request.GET.get('action')
    model_name = request.GET.get('model')

    # Build queryset
    start_date = timezone.now() - timedelta(days=days)
    logs = AuditLog.objects.filter(
        timestamp__gte=start_date
    ).select_related('user', 'content_type').order_by('-timestamp')

    if user_filter:
        logs = logs.filter(username=user_filter)

    if action:
        logs = logs.filter(action=action)

    if model_name:
        logs = logs.filter(model_name=model_name)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get unique models and actions for filters
    models = AuditLog.objects.values_list('model_name', flat=True).distinct()
    actions = AuditLog.ACTION_CHOICES

    context = {
        'page_obj': page_obj,
        'days': days,
        'user_filter': user_filter,
        'action': action,
        'model_name': model_name,
        'models': models,
        'actions': actions,
    }

    return render(request, 'core/audit_logs.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def system_events(request):
    """
    System events viewer

    URL: /core/system-events/
    """
    # Filters
    days = int(request.GET.get('days', 7))
    level = request.GET.get('level')
    category = request.GET.get('category')
    unresolved_only = request.GET.get('unresolved') == 'true'

    # Build queryset
    start_date = timezone.now() - timedelta(days=days)
    events = SystemEvent.objects.filter(
        timestamp__gte=start_date
    ).order_by('-timestamp')

    if level:
        events = events.filter(level=level)

    if category:
        events = events.filter(category=category)

    if unresolved_only:
        events = events.filter(is_resolved=False)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(events, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter options
    levels = SystemEvent.EVENT_LEVELS
    categories = SystemEvent.EVENT_CATEGORIES

    context = {
        'page_obj': page_obj,
        'days': days,
        'level': level,
        'category': category,
        'unresolved_only': unresolved_only,
        'levels': levels,
        'categories': categories,
    }

    return render(request, 'core/system_events.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def user_activity_report(request, username):
    """
    Individual user activity report

    URL: /core/user-activity/<username>/
    """
    from django.contrib.auth.models import User
    from django.shortcuts import get_object_or_404

    user = get_object_or_404(User, username=username)
    days = int(request.GET.get('days', 30))

    # Get activity summary
    summary = get_user_activity_summary(user, days=days)

    # Recent activities
    recent_activities = ActivityLog.objects.filter(
        user=user,
        timestamp__gte=timezone.now() - timedelta(days=days)
    ).order_by('-timestamp')[:50]

    # Recent audits
    recent_audits = AuditLog.objects.filter(
        user=user,
        timestamp__gte=timezone.now() - timedelta(days=days)
    ).order_by('-timestamp')[:50]

    context = {
        'report_user': user,
        'days': days,
        'summary': summary,
        'recent_activities': recent_activities,
        'recent_audits': recent_audits,
    }

    return render(request, 'core/user_activity_report.html', context)


# ============================================================================
# EXPORT VIEWS
# ============================================================================

@login_required
@user_passes_test(is_staff_or_superuser)
def export_activity_logs(request):
    """
    Export activity logs to Excel/CSV/PDF

    URL: /core/export/activity-logs/?format=excel
    """
    export_format = request.GET.get('format', 'excel')
    days = int(request.GET.get('days', 30))

    start_date = timezone.now() - timedelta(days=days)
    queryset = ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).select_related('user')

    fields = ['timestamp', 'user__username', 'activity_type', 'path', 'duration_ms', 'ip_address']
    headers = ['Timestamp', 'User', 'Activity Type', 'Path', 'Duration (ms)', 'IP Address']

    filename = f'activity_logs_{timezone.now().strftime("%Y%m%d")}'

    if export_format == 'excel':
        return export_queryset_to_excel(
            queryset, f'{filename}.xlsx', 'Activity Logs', fields, headers
        )
    elif export_format == 'pdf':
        return export_queryset_to_pdf(
            queryset, f'{filename}.pdf', 'Activity Logs', fields, headers
        )
    else:  # csv
        return export_queryset_to_csv(
            queryset, f'{filename}.csv', fields, headers
        )


@login_required
@user_passes_test(is_staff_or_superuser)
def export_audit_logs(request):
    """
    Export audit logs to Excel/CSV/PDF

    URL: /core/export/audit-logs/?format=excel
    """
    export_format = request.GET.get('format', 'excel')
    days = int(request.GET.get('days', 30))

    start_date = timezone.now() - timedelta(days=days)
    queryset = AuditLog.objects.filter(
        timestamp__gte=start_date
    ).select_related('user')

    fields = ['timestamp', 'username', 'action', 'model_name', 'object_repr', 'message', 'ip_address']
    headers = ['Timestamp', 'User', 'Action', 'Model', 'Object', 'Message', 'IP Address']

    filename = f'audit_logs_{timezone.now().strftime("%Y%m%d")}'

    if export_format == 'excel':
        return export_queryset_to_excel(
            queryset, f'{filename}.xlsx', 'Audit Logs', fields, headers
        )
    elif export_format == 'pdf':
        return export_queryset_to_pdf(
            queryset, f'{filename}.pdf', 'Audit Logs', fields, headers
        )
    else:  # csv
        return export_queryset_to_csv(
            queryset, f'{filename}.csv', fields, headers
        )


# ============================================================================
# API VIEWS (JSON)
# ============================================================================

@login_required
@user_passes_test(is_staff_or_superuser)
def api_system_health(request):
    """
    API endpoint for system health

    URL: /core/api/health/
    Returns: JSON
    """
    health = get_system_health_summary()

    # Convert datetime to string
    health['timestamp'] = health['timestamp'].isoformat()

    return JsonResponse(health)


@login_required
@user_passes_test(is_staff_or_superuser)
def api_activity_stats(request):
    """
    API endpoint for activity statistics

    URL: /core/api/activity-stats/?days=7
    Returns: JSON
    """
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)

    # Activity by type
    by_type = list(ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count'))

    # Activity by hour
    from django.db.models.functions import ExtractHour
    by_hour = list(ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).annotate(
        hour=ExtractHour('timestamp')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour'))

    # Top users
    top_users = list(ActivityLog.objects.filter(
        timestamp__gte=start_date
    ).values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:10])

    return JsonResponse({
        'by_type': by_type,
        'by_hour': by_hour,
        'top_users': top_users,
        'date_range': {
            'start': start_date.isoformat(),
            'end': timezone.now().isoformat(),
        }
    })


@login_required
@user_passes_test(is_staff_or_superuser)
def api_audit_stats(request):
    """
    API endpoint for audit statistics

    URL: /core/api/audit-stats/?days=7
    Returns: JSON
    """
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)

    # Actions by type
    by_action = list(AuditLog.objects.filter(
        timestamp__gte=start_date
    ).values('action').annotate(
        count=Count('id')
    ).order_by('-count'))

    # By model
    by_model = list(AuditLog.objects.filter(
        timestamp__gte=start_date
    ).values('model_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10])

    # By user
    by_user = list(AuditLog.objects.filter(
        timestamp__gte=start_date
    ).values('username').annotate(
        count=Count('id')
    ).order_by('-count')[:10])

    return JsonResponse({
        'by_action': by_action,
        'by_model': by_model,
        'by_user': by_user,
        'date_range': {
            'start': start_date.isoformat(),
            'end': timezone.now().isoformat(),
        }
    })
