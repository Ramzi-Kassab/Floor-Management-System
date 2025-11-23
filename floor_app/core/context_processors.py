"""
Context processors for core system

Provides global template context for system information
"""
from django.utils import timezone
from datetime import timedelta
from .models import SystemEvent, ActivityLog


def system_status(request):
    """
    Add system status to template context

    Available in all templates as:
    - {{ system_status.unresolved_errors }}
    - {{ system_status.critical_events }}
    - {{ system_status.recent_activity_count }}
    """
    if not request.user.is_authenticated:
        return {}

    # Only calculate for staff users
    if not (request.user.is_staff or request.user.is_superuser):
        return {}

    # Get counts for last 24 hours
    last_24h = timezone.now() - timedelta(hours=24)

    try:
        unresolved_errors = SystemEvent.objects.filter(
            level__in=['ERROR', 'CRITICAL'],
            is_resolved=False,
            timestamp__gte=last_24h
        ).count()

        critical_events = SystemEvent.objects.filter(
            level='CRITICAL',
            timestamp__gte=last_24h
        ).count()

        recent_activity_count = ActivityLog.objects.filter(
            timestamp__gte=last_24h
        ).count()

        return {
            'system_status': {
                'unresolved_errors': unresolved_errors,
                'critical_events': critical_events,
                'recent_activity_count': recent_activity_count,
                'has_alerts': unresolved_errors > 0 or critical_events > 0,
            }
        }
    except Exception:
        # Don't break template rendering if there's an error
        return {}


def user_activity(request):
    """
    Add current user's recent activity to template context

    Available in all templates as:
    - {{ user_recent_activities }}
    """
    if not request.user.is_authenticated:
        return {}

    try:
        last_7_days = timezone.now() - timedelta(days=7)

        recent_activities = ActivityLog.objects.filter(
            user=request.user,
            timestamp__gte=last_7_days
        ).order_by('-timestamp')[:10]

        return {
            'user_recent_activities': recent_activities,
        }
    except Exception:
        return {}
