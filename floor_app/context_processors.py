"""
Context processors for Floor App.

These functions add variables to the template context for all templates.
"""

from django.contrib.auth.models import User
from django.utils import timezone


def system_context(request):
    """
    Add common system-wide data to all template contexts.

    Available in all templates:
    - unread_notifications_count
    - user_has_pending_tasks
    - system_name
    - current_year
    - is_maintenance_mode
    """
    context = {
        'system_name': 'Floor Management System',
        'current_year': timezone.now().year,
        'is_maintenance_mode': False,  # TODO: Check actual maintenance mode
    }

    # Add user-specific data if authenticated
    if request.user.is_authenticated:
        # TODO: Replace with actual queries when models are implemented
        context['unread_notifications_count'] = 5
        context['user_has_pending_tasks'] = False
        context['user_full_name'] = request.user.get_full_name() or request.user.username

    return context


def navigation_context(request):
    """
    Add navigation-related data to template context.

    Available in all templates:
    - active_module
    - breadcrumbs
    """
    # Determine active module from URL
    path = request.path
    active_module = None

    if '/hr/' in path:
        active_module = 'hr'
    elif '/inventory/' in path:
        active_module = 'inventory'
    elif '/production/' in path:
        active_module = 'production'
    elif '/quality/' in path:
        active_module = 'quality'
    elif '/analytics/' in path:
        active_module = 'analytics'
    elif '/sales/' in path:
        active_module = 'sales'

    context = {
        'active_module': active_module,
        'current_path': path,
    }

    return context


def user_permissions_context(request):
    """
    Add user permissions data to template context.

    Available in all templates:
    - user_is_admin
    - user_is_staff
    - user_can_manage_users
    - user_can_view_analytics
    """
    if not request.user.is_authenticated:
        return {
            'user_is_admin': False,
            'user_is_staff': False,
            'user_can_manage_users': False,
            'user_can_view_analytics': False,
        }

    user = request.user

    context = {
        'user_is_admin': user.is_superuser,
        'user_is_staff': user.is_staff,
        'user_can_manage_users': user.is_staff or user.is_superuser,
        'user_can_view_analytics': user.is_staff or user.is_superuser,
    }

    # Add specific permissions
    if user.is_authenticated:
        context['user_can_edit_profile'] = True
        context['user_can_view_reports'] = True

    return context


def stats_context(request):
    """
    Add system statistics to template context.

    Available in all templates:
    - total_users
    - active_users
    - system_health
    """
    # Only add stats for staff/admin users
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return {}

    try:
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()

        context = {
            'total_users': total_users,
            'active_users': active_users,
            'system_health': 'good',  # TODO: Implement actual health check
        }
    except Exception:
        # Fallback if database is not available
        context = {
            'total_users': 0,
            'active_users': 0,
            'system_health': 'unknown',
        }

    return context
