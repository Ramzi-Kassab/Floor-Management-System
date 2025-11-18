"""
Notification and Activity Logging Utilities

Provides easy-to-use functions for creating notifications and logging activities.
"""

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


def create_notification(user, title, message, notification_type='INFO', priority='NORMAL',
                       related_object=None, action_url='', action_text='View', created_by=None):
    """
    Create a notification for a user.

    Args:
        user: User or list of users to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification (INFO, SUCCESS, WARNING, ERROR, TASK, APPROVAL, SYSTEM)
        priority: Priority level (LOW, NORMAL, HIGH, URGENT)
        related_object: Optional related Django model instance
        action_url: Optional URL for action button
        action_text: Text for action button
        created_by: User who created the notification

    Returns:
        List of created Notification objects
    """
    from core.models import Notification

    # Handle single user or list of users
    users = [user] if not isinstance(user, (list, tuple)) else user

    notifications = []
    for recipient in users:
        notification = Notification(
            user=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            action_text=action_text,
            created_by=created_by
        )

        # Link to related object if provided
        if related_object:
            notification.content_type = ContentType.objects.get_for_model(related_object)
            notification.object_id = related_object.pk

        notification.save()
        notifications.append(notification)

    return notifications


def notify_users(users, title, message, **kwargs):
    """
    Notify multiple users.

    Args:
        users: QuerySet or list of User objects
        title: Notification title
        message: Notification message
        **kwargs: Additional notification parameters

    Returns:
        List of created notifications
    """
    return create_notification(list(users), title, message, **kwargs)


def notify_admins(title, message, **kwargs):
    """
    Notify all admin users.

    Args:
        title: Notification title
        message: Notification message
        **kwargs: Additional notification parameters

    Returns:
        List of created notifications
    """
    admins = User.objects.filter(is_staff=True, is_active=True)
    return notify_users(admins, title, message, **kwargs)


def notify_superusers(title, message, **kwargs):
    """
    Notify all superusers.

    Args:
        title: Notification title
        message: Notification message
        **kwargs: Additional notification parameters

    Returns:
        List of created notifications
    """
    superusers = User.objects.filter(is_superuser=True, is_active=True)
    return notify_users(superusers, title, message, **kwargs)


def log_activity(user, action, description, related_object=None, extra_data=None, request=None):
    """
    Log an activity/action.

    Args:
        user: User who performed the action
        action: Type of action (CREATE, UPDATE, DELETE, VIEW, etc.)
        description: Description of the action
        related_object: Optional related Django model instance
        extra_data: Optional dictionary of additional data
        request: Optional HttpRequest object to capture IP and user agent

    Returns:
        ActivityLog object
    """
    from core.models import ActivityLog

    activity = ActivityLog(
        user=user,
        action=action,
        description=description,
        extra_data=extra_data or {}
    )

    # Link to related object if provided
    if related_object:
        activity.content_type = ContentType.objects.get_for_model(related_object)
        activity.object_id = related_object.pk

    # Capture request info if provided
    if request:
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        activity.ip_address = ip_address

        # Get user agent
        activity.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    activity.save()
    return activity


def log_create(user, obj, description=None, request=None):
    """Log object creation."""
    desc = description or f"Created {obj._meta.verbose_name}: {str(obj)}"
    return log_activity(user, 'CREATE', desc, related_object=obj, request=request)


def log_update(user, obj, description=None, changes=None, request=None):
    """Log object update."""
    desc = description or f"Updated {obj._meta.verbose_name}: {str(obj)}"
    extra = {'changes': changes} if changes else None
    return log_activity(user, 'UPDATE', desc, related_object=obj, extra_data=extra, request=request)


def log_delete(user, obj, description=None, request=None):
    """Log object deletion."""
    desc = description or f"Deleted {obj._meta.verbose_name}: {str(obj)}"
    # Store object info before deletion
    extra = {
        'object_str': str(obj),
        'object_repr': repr(obj)
    }
    return log_activity(user, 'DELETE', desc, extra_data=extra, request=request)


def log_view(user, obj, description=None, request=None):
    """Log object view."""
    desc = description or f"Viewed {obj._meta.verbose_name}: {str(obj)}"
    return log_activity(user, 'VIEW', desc, related_object=obj, request=request)


def log_export(user, model_name, record_count, export_format, request=None):
    """Log data export."""
    desc = f"Exported {record_count} {model_name} records to {export_format.upper()}"
    extra = {
        'model': model_name,
        'count': record_count,
        'format': export_format
    }
    return log_activity(user, 'EXPORT', desc, extra_data=extra, request=request)


def get_unread_notifications(user):
    """Get user's unread notifications."""
    from core.models import Notification
    return Notification.objects.filter(user=user, is_read=False).order_by('-created_at')


def get_unread_count(user):
    """Get count of user's unread notifications."""
    from core.models import Notification
    return Notification.objects.filter(user=user, is_read=False).count()


def mark_all_read(user):
    """Mark all user's notifications as read."""
    from core.models import Notification
    unread = Notification.objects.filter(user=user, is_read=False)
    count = unread.count()
    for notification in unread:
        notification.mark_as_read()
    return count


def get_recent_activities(user=None, limit=50):
    """
    Get recent activities.

    Args:
        user: Optional user to filter by
        limit: Maximum number of activities to return

    Returns:
        QuerySet of ActivityLog objects
    """
    from core.models import ActivityLog

    if user:
        return ActivityLog.objects.filter(user=user).order_by('-created_at')[:limit]
    return ActivityLog.objects.all().order_by('-created_at')[:limit]


def get_object_activities(obj, limit=50):
    """Get activities related to a specific object."""
    from core.models import ActivityLog
    content_type = ContentType.objects.get_for_model(obj)
    return ActivityLog.objects.filter(
        content_type=content_type,
        object_id=obj.pk
    ).order_by('-created_at')[:limit]


def cleanup_old_notifications(days=90):
    """
    Clean up old read notifications.

    Args:
        days: Delete read notifications older than this many days

    Returns:
        Number of notifications deleted
    """
    from core.models import Notification
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)
    old_notifications = Notification.objects.filter(
        is_read=True,
        read_at__lt=cutoff_date
    )
    count = old_notifications.count()
    old_notifications.delete()
    return count


def cleanup_old_activities(days=365):
    """
    Clean up old activity logs.

    Args:
        days: Delete activities older than this many days

    Returns:
        Number of activities deleted
    """
    from core.models import ActivityLog
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)
    old_activities = ActivityLog.objects.filter(created_at__lt=cutoff_date)
    count = old_activities.count()
    old_activities.delete()
    return count


# Decorator for automatic activity logging
def log_action(action_type='UPDATE', description_template=None):
    """
    Decorator to automatically log actions.

    Usage:
        @log_action(action_type='UPDATE', description_template='Updated item {obj}')
        def update_item(request, item):
            # ... update code ...
            return item
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)

            # Try to extract request and object
            request = None
            obj = None
            user = None

            # Look for request in args/kwargs
            for arg in args:
                if hasattr(arg, 'user') and hasattr(arg, 'META'):
                    request = arg
                    user = request.user if hasattr(request, 'user') else None
                    break

            # Look for model instance
            if result and hasattr(result, '_meta'):
                obj = result

            # Generate description
            if description_template and obj:
                desc = description_template.format(obj=str(obj))
            elif obj:
                desc = f"{action_type.capitalize()} {obj._meta.verbose_name}: {str(obj)}"
            else:
                desc = f"{action_type.capitalize()} action performed"

            # Log if we have a user
            if user and user.is_authenticated:
                log_activity(user, action_type, desc, related_object=obj, request=request)

            return result
        return wrapper
    return decorator
