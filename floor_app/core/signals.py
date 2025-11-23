"""
Signal handlers for automatic audit logging

This module provides automatic audit logging for all model changes
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog, SystemEvent


# ============================================================================
# AUTHENTICATION SIGNALS
# ============================================================================

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    AuditLog.log_action(
        user=user,
        action='LOGIN',
        message=f'User {user.username} logged in successfully',
        ip_address=ip_address,
        user_agent=user_agent
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    if user:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        AuditLog.log_action(
            user=user,
            action='LOGOUT',
            message=f'User {user.username} logged out',
            ip_address=ip_address,
            user_agent=user_agent
        )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempts"""
    username = credentials.get('username', 'unknown')
    ip_address = get_client_ip(request)

    SystemEvent.log_event(
        level='WARNING',
        category='SECURITY',
        event_name='Failed Login Attempt',
        message=f'Failed login attempt for username: {username}',
        request=request,
        username=username
    )


# ============================================================================
# MODEL CHANGE SIGNALS
# ============================================================================

def should_audit_model(model_class):
    """
    Determine if a model should be audited

    Exclude audit models themselves and some Django internal models
    """
    from .models import AuditLog, ChangeHistory, ActivityLog, SystemEvent

    excluded_models = [
        AuditLog,
        ChangeHistory,
        ActivityLog,
        SystemEvent,
        ContentType,
    ]

    # Exclude session and migration models
    model_name = model_class.__name__
    if model_name in ['Session', 'Migration', 'LogEntry']:
        return False

    return model_class not in excluded_models


@receiver(post_save)
def audit_model_save(sender, instance, created, **kwargs):
    """
    Automatically audit model saves

    Can be disabled by passing audit=False to save()
    """
    # Check if auditing is disabled for this save
    if kwargs.get('raw', False):  # Don't audit during loaddata
        return

    # Check if model should be audited
    if not should_audit_model(sender):
        return

    # Get request context if available
    context = get_request_context()

    action = 'CREATE' if created else 'UPDATE'

    try:
        AuditLog.log_action(
            user=context.get('user'),
            action=action,
            obj=instance,
            message=f'{action} {sender.__name__}: {str(instance)[:200]}',
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent'),
        )
    except Exception:
        # Don't break the save if audit logging fails
        pass


@receiver(pre_delete)
def audit_model_delete(sender, instance, **kwargs):
    """
    Automatically audit model deletions
    """
    # Check if model should be audited
    if not should_audit_model(sender):
        return

    # Get request context if available
    context = get_request_context()

    try:
        AuditLog.log_action(
            user=context.get('user'),
            action='DELETE',
            obj=instance,
            message=f'DELETE {sender.__name__}: {str(instance)[:200]}',
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent'),
        )
    except Exception:
        # Don't break the delete if audit logging fails
        pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_request_context():
    """
    Get current request context from thread-local storage

    Returns dict with user, ip_address, user_agent
    """
    try:
        # Try to get from middleware
        import threading
        current_thread = threading.current_thread()

        # Look for request in thread
        if hasattr(current_thread, '_audit_context'):
            return current_thread._audit_context

        # Try alternative methods
        for attr in dir(current_thread):
            obj = getattr(current_thread, attr, None)
            if hasattr(obj, '_audit_context'):
                return obj._audit_context

        return {}
    except Exception:
        return {}


# ============================================================================
# SIGNAL REGISTRATION HELPERS
# ============================================================================

def connect_audit_signals():
    """
    Manually connect audit signals to all models

    This is an alternative to using @receiver decorators
    """
    from django.apps import apps

    # Get all models
    all_models = apps.get_models()

    for model in all_models:
        if should_audit_model(model):
            post_save.connect(audit_model_save, sender=model, weak=False)
            pre_delete.connect(audit_model_delete, sender=model, weak=False)


def disconnect_audit_signals():
    """
    Disconnect audit signals (useful for testing)
    """
    from django.apps import apps

    all_models = apps.get_models()

    for model in all_models:
        post_save.disconnect(audit_model_save, sender=model)
        pre_delete.disconnect(audit_model_delete, sender=model)
