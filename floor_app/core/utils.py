"""
Utility functions for audit logging and change tracking
"""
from django.contrib.contenttypes.models import ContentType
from .models import ChangeHistory, AuditLog


def track_model_changes(old_instance, new_instance, user=None, ip_address=None, change_reason=''):
    """
    Track changes between two model instances

    Usage:
        old_employee = Employee.objects.get(pk=1)
        # User makes changes
        employee.employment_status = 'TERMINATED'
        employee.save()
        track_model_changes(old_employee, employee, user=request.user)

    Args:
        old_instance: The instance before changes
        new_instance: The instance after changes
        user: The user who made the changes
        ip_address: IP address of the user
        change_reason: Reason for the change
    """
    if old_instance.__class__ != new_instance.__class__:
        raise ValueError("Instances must be of the same model")

    # Get all fields from the model
    fields_to_track = [
        field.name for field in old_instance._meta.fields
        if not field.name.startswith('_')
    ]

    # Track changes
    field_changes = {}
    for field_name in fields_to_track:
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(new_instance, field_name, None)

        # Convert to string for comparison
        old_str = str(old_value) if old_value is not None else ''
        new_str = str(new_value) if new_value is not None else ''

        if old_str != new_str:
            field_changes[field_name] = {
                'old': old_str,
                'new': new_str
            }

    # Only create history entry if there are changes
    if field_changes:
        # Create change summary
        change_summary = ', '.join([
            f"{field}: '{values['old']}' → '{values['new']}'"
            for field, values in field_changes.items()
        ])

        # Create ChangeHistory entry
        ChangeHistory.objects.create(
            content_object=new_instance,
            field_changes=field_changes,
            change_summary=change_summary,
            changed_by=user,
            change_reason=change_reason,
            ip_address=ip_address
        )

        # Also create AuditLog entries for each field change
        for field_name, values in field_changes.items():
            AuditLog.log_action(
                user=user,
                action='UPDATE',
                obj=new_instance,
                field_name=field_name,
                old_value=values['old'],
                new_value=values['new'],
                message=f"Updated {field_name}",
                ip_address=ip_address
            )

    return field_changes


def get_change_history(obj, limit=None):
    """
    Get change history for an object

    Usage:
        history = get_change_history(employee, limit=10)
        for change in history:
            print(f"{change.changed_at}: {change.get_changes_display()}")

    Args:
        obj: The model instance
        limit: Optional limit on number of results

    Returns:
        QuerySet of ChangeHistory objects
    """
    content_type = ContentType.objects.get_for_model(obj)
    queryset = ChangeHistory.objects.filter(
        content_type=content_type,
        object_id=str(obj.pk)
    ).select_related('changed_by')

    if limit:
        queryset = queryset[:limit]

    return queryset


def get_audit_trail(obj, limit=None):
    """
    Get audit trail for an object

    Usage:
        audit_trail = get_audit_trail(employee, limit=20)
        for entry in audit_trail:
            print(f"{entry.timestamp}: {entry.action} by {entry.username}")

    Args:
        obj: The model instance
        limit: Optional limit on number of results

    Returns:
        QuerySet of AuditLog objects
    """
    content_type = ContentType.objects.get_for_model(obj)
    queryset = AuditLog.objects.filter(
        content_type=content_type,
        object_id=str(obj.pk)
    )

    if limit:
        queryset = queryset[:limit]

    return queryset


def log_action(user, action, obj=None, message='', request=None, **kwargs):
    """
    Convenience wrapper for logging actions

    Usage:
        log_action(
            user=request.user,
            action='APPROVE',
            obj=leave_request,
            message='Approved leave request',
            request=request
        )

    Args:
        user: User performing the action
        action: Action type (CREATE, UPDATE, DELETE, etc.)
        obj: Optional object being acted upon
        message: Description of the action
        request: Optional Django request object
        **kwargs: Additional fields for AuditLog
    """
    # Extract info from request if provided
    ip_address = None
    user_agent = None

    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    return AuditLog.log_action(
        user=user,
        action=action,
        obj=obj,
        message=message,
        ip_address=ip_address,
        user_agent=user_agent,
        **kwargs
    )


class ChangeTracker:
    """
    Context manager for tracking changes to a model instance

    Usage:
        with ChangeTracker(employee, user=request.user, reason='Annual review'):
            employee.salary = 60000
            employee.position = new_position
            employee.save()
        # Changes are automatically tracked when context exits
    """

    def __init__(self, instance, user=None, ip_address=None, change_reason=''):
        """
        Initialize the change tracker

        Args:
            instance: The model instance to track
            user: The user making changes
            ip_address: IP address of the user
            change_reason: Reason for the changes
        """
        self.instance = instance
        self.user = user
        self.ip_address = ip_address
        self.change_reason = change_reason
        self.original_state = {}

    def __enter__(self):
        """Store the original state when entering context"""
        # Store original values of all fields
        for field in self.instance._meta.fields:
            field_name = field.name
            self.original_state[field_name] = getattr(self.instance, field_name, None)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Track changes when exiting context"""
        # If there was an exception, don't track changes
        if exc_type is not None:
            return False

        # Create a temporary object with original state for comparison
        from copy import copy
        old_instance = copy(self.instance)
        for field_name, value in self.original_state.items():
            setattr(old_instance, field_name, value)

        # Track the changes
        track_model_changes(
            old_instance,
            self.instance,
            user=self.user,
            ip_address=self.ip_address,
            change_reason=self.change_reason
        )

        return False


def get_user_activity_summary(user, days=30):
    """
    Get activity summary for a user over the last N days

    Usage:
        summary = get_user_activity_summary(user, days=7)
        print(f"Total activities: {summary['total_count']}")
        print(f"Page views: {summary['by_type']['PAGE_VIEW']}")

    Args:
        user: User object
        days: Number of days to look back

    Returns:
        Dictionary with activity statistics
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import ActivityLog

    start_date = timezone.now() - timedelta(days=days)

    activities = ActivityLog.objects.filter(
        user=user,
        timestamp__gte=start_date
    )

    # Count by activity type
    by_type = {}
    for activity_type, _ in ActivityLog.ACTIVITY_TYPES:
        count = activities.filter(activity_type=activity_type).count()
        if count > 0:
            by_type[activity_type] = count

    # Get most visited paths
    from django.db.models import Count
    top_paths = activities.values('path').annotate(
        count=Count('path')
    ).order_by('-count')[:10]

    # Calculate average duration
    activities_with_duration = activities.exclude(duration_ms__isnull=True)
    avg_duration = None
    if activities_with_duration.exists():
        from django.db.models import Avg
        avg_duration = activities_with_duration.aggregate(
            avg=Avg('duration_ms')
        )['avg']

    return {
        'total_count': activities.count(),
        'by_type': by_type,
        'top_paths': list(top_paths),
        'avg_duration_ms': avg_duration,
        'date_range': {
            'start': start_date,
            'end': timezone.now()
        }
    }


def get_system_health_summary():
    """
    Get system health summary based on recent events

    Usage:
        health = get_system_health_summary()
        if health['error_count'] > 10:
            send_alert()

    Returns:
        Dictionary with system health metrics
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import SystemEvent

    # Last 24 hours
    last_24h = timezone.now() - timedelta(hours=24)

    events = SystemEvent.objects.filter(timestamp__gte=last_24h)

    # Count by level
    error_count = events.filter(level='ERROR').count()
    warning_count = events.filter(level='WARNING').count()
    critical_count = events.filter(level='CRITICAL').count()

    # Unresolved events
    unresolved_count = events.filter(is_resolved=False).count()

    # Most common errors
    from django.db.models import Count
    common_errors = events.filter(
        level__in=['ERROR', 'CRITICAL']
    ).values('event_name').annotate(
        count=Count('event_name')
    ).order_by('-count')[:5]

    # Determine overall health status
    if critical_count > 0 or error_count > 50:
        health_status = 'CRITICAL'
    elif error_count > 10 or warning_count > 100:
        health_status = 'WARNING'
    elif error_count > 0 or warning_count > 0:
        health_status = 'DEGRADED'
    else:
        health_status = 'HEALTHY'

    return {
        'health_status': health_status,
        'error_count': error_count,
        'warning_count': warning_count,
        'critical_count': critical_count,
        'unresolved_count': unresolved_count,
        'common_errors': list(common_errors),
        'timestamp': timezone.now()
    }


def cleanup_old_logs(days=90):
    """
    Clean up old audit logs, activity logs, and resolved system events

    Usage:
        # In a scheduled task or management command
        deleted_counts = cleanup_old_logs(days=90)
        print(f"Deleted {deleted_counts['audit_logs']} audit logs")

    Args:
        days: Number of days to keep (delete older than this)

    Returns:
        Dictionary with counts of deleted records
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import ActivityLog, SystemEvent

    cutoff_date = timezone.now() - timedelta(days=days)

    # Delete old activity logs
    activity_count, _ = ActivityLog.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()

    # Delete old resolved system events
    event_count, _ = SystemEvent.objects.filter(
        timestamp__lt=cutoff_date,
        is_resolved=True
    ).delete()

    # Note: We don't delete AuditLog or ChangeHistory by default
    # as they may be required for compliance

    return {
        'activity_logs': activity_count,
        'resolved_events': event_count,
        'cutoff_date': cutoff_date
    }
