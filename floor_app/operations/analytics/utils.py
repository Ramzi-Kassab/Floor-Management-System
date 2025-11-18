"""
Utility functions for analytics module
"""
import re
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_user_agent(user_agent):
    """Parse user agent string to extract device, browser, and OS information"""
    if not user_agent:
        return {
            'device_type': 'Unknown',
            'browser': 'Unknown',
            'os': 'Unknown'
        }

    user_agent_lower = user_agent.lower()

    # Detect device type
    if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
        device_type = 'Mobile'
    elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'

    # Detect browser
    browser = 'Unknown'
    if 'edg' in user_agent_lower:
        browser = 'Edge'
    elif 'chrome' in user_agent_lower and 'edg' not in user_agent_lower:
        browser = 'Chrome'
    elif 'firefox' in user_agent_lower:
        browser = 'Firefox'
    elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
        browser = 'Safari'
    elif 'opera' in user_agent_lower or 'opr' in user_agent_lower:
        browser = 'Opera'
    elif 'msie' in user_agent_lower or 'trident' in user_agent_lower:
        browser = 'Internet Explorer'

    # Detect OS
    os_name = 'Unknown'
    if 'windows' in user_agent_lower:
        os_name = 'Windows'
    elif 'mac os' in user_agent_lower or 'macos' in user_agent_lower:
        os_name = 'macOS'
    elif 'linux' in user_agent_lower:
        os_name = 'Linux'
    elif 'android' in user_agent_lower:
        os_name = 'Android'
    elif 'ios' in user_agent_lower or 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
        os_name = 'iOS'

    return {
        'device_type': device_type,
        'browser': browser,
        'os': os_name
    }


def get_module_from_url(url_name):
    """Extract module name from URL name"""
    if not url_name:
        return ''

    # URL names follow pattern: module:view_name
    if ':' in url_name:
        return url_name.split(':')[0]

    # Fallback: try to extract from URL name
    module_keywords = ['hr', 'inventory', 'production', 'evaluation', 'qrcodes',
                      'purchasing', 'knowledge', 'maintenance', 'quality',
                      'planning', 'sales', 'core', 'analytics']

    for keyword in module_keywords:
        if keyword in url_name.lower():
            return keyword

    return 'other'


def calculate_active_users(hours=24):
    """Calculate number of active users in the last X hours"""
    from .models import UserSession
    cutoff_time = timezone.now() - timedelta(hours=hours)
    return UserSession.objects.filter(
        last_activity__gte=cutoff_time,
        is_active=True
    ).values('user').distinct().count()


def get_top_users_by_activity(days=30, limit=10):
    """Get most active users by activity count"""
    from .models import UserActivity
    from django.db.models import Count
    cutoff_date = timezone.now() - timedelta(days=days)

    return UserActivity.objects.filter(
        timestamp__gte=cutoff_date
    ).values('user__username', 'user__first_name', 'user__last_name').annotate(
        activity_count=Count('id')
    ).order_by('-activity_count')[:limit]


def get_popular_pages(days=30, limit=10):
    """Get most viewed pages"""
    from .models import PageView
    from django.db.models import Count
    cutoff_date = timezone.now() - timedelta(days=days)

    return PageView.objects.filter(
        timestamp__gte=cutoff_date
    ).values('url', 'url_name').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:limit]


def get_module_usage_stats(days=30):
    """Get usage statistics by module"""
    from .models import PageView, UserActivity
    from django.db.models import Count
    cutoff_date = timezone.now() - timedelta(days=days)

    # Page views by module
    page_views = PageView.objects.filter(
        timestamp__gte=cutoff_date,
        module__isnull=False
    ).exclude(module='').values('module').annotate(
        count=Count('id')
    ).order_by('-count')

    # Activities by module
    activities = UserActivity.objects.filter(
        timestamp__gte=cutoff_date,
        module__isnull=False
    ).exclude(module='').values('module').annotate(
        count=Count('id')
    ).order_by('-count')

    # Combine results
    result = {}
    for pv in page_views:
        result[pv['module']] = {
            'page_views': pv['count'],
            'activities': 0
        }

    for act in activities:
        if act['module'] in result:
            result[act['module']]['activities'] = act['count']
        else:
            result[act['module']] = {
                'page_views': 0,
                'activities': act['count']
            }

    return result


def get_error_summary(days=7):
    """Get error summary for the last X days"""
    from .models import ErrorLog
    from django.db.models import Count
    cutoff_date = timezone.now() - timedelta(days=days)

    errors = ErrorLog.objects.filter(
        timestamp__gte=cutoff_date
    )

    return {
        'total': errors.count(),
        'critical': errors.filter(severity='critical').count(),
        'errors': errors.filter(severity='error').count(),
        'warnings': errors.filter(severity='warning').count(),
        'by_type': errors.values('error_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10],
        'by_module': errors.exclude(module='').values('module').annotate(
            count=Count('id')
        ).order_by('-count')[:10],
        'unresolved': errors.filter(is_resolved=False).count(),
    }


def get_search_insights(days=30, limit=10):
    """Get popular search terms and low-result searches"""
    from .models import SearchQuery
    from django.db.models import Count, Avg
    cutoff_date = timezone.now() - timedelta(days=days)

    queries = SearchQuery.objects.filter(timestamp__gte=cutoff_date)

    # Most popular searches
    popular = queries.values('search_term', 'module').annotate(
        count=Count('id')
    ).order_by('-count')[:limit]

    # Low-result searches (potential improvements needed)
    low_results = queries.filter(results_count__lt=3).values('search_term', 'module').annotate(
        count=Count('id'),
        avg_results=Avg('results_count')
    ).order_by('-count')[:limit]

    # Searches with no clicks (users didn't find what they wanted)
    no_clicks = queries.filter(clicked_result=False).values('search_term', 'module').annotate(
        count=Count('id')
    ).order_by('-count')[:limit]

    return {
        'popular': popular,
        'low_results': low_results,
        'no_clicks': no_clicks,
    }


def generate_user_activity_report(user, days=30):
    """Generate comprehensive activity report for a user"""
    from .models import UserActivity, PageView, UserSession
    from django.db.models import Count, Sum, Avg
    cutoff_date = timezone.now() - timedelta(days=days)

    # Sessions
    sessions = UserSession.objects.filter(
        user=user,
        login_time__gte=cutoff_date
    )

    # Activities
    activities = UserActivity.objects.filter(
        user=user,
        timestamp__gte=cutoff_date
    )

    # Page views
    page_views = PageView.objects.filter(
        user=user,
        timestamp__gte=cutoff_date
    )

    return {
        'user': user,
        'period_days': days,
        'total_sessions': sessions.count(),
        'total_login_time': sessions.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0,
        'avg_session_duration': sessions.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0,
        'total_page_views': page_views.count(),
        'total_activities': activities.count(),
        'activities_by_type': activities.values('action_type').annotate(
            count=Count('id')
        ).order_by('-count'),
        'activities_by_module': activities.values('module').annotate(
            count=Count('id')
        ).order_by('-count'),
        'popular_pages': page_views.values('url', 'url_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10],
    }
