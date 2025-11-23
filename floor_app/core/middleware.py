"""
Custom middleware for the Floor Management System

Provides:
- Activity logging
- Audit trail capture
- Request/response timing
- User tracking
- Error monitoring
"""
import time
import json
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import AuditLog, ActivityLog, SystemEvent


class ActivityTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user activity across the application

    Logs page views, API calls, and user navigation
    """

    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/admin/jsi18n/',
        '/favicon.ico',
        '/__debug__/',
    ]

    def process_request(self, request):
        """Mark the start time of the request"""
        request._start_time = time.time()
        return None

    def process_response(self, request, response):
        """Log the activity after request completes"""
        # Skip if user is not authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response

        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response

        # Calculate duration
        duration_ms = None
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            duration_ms = int(duration * 1000)

        # Determine activity type
        activity_type = self._determine_activity_type(request)

        # Skip if no meaningful activity
        if not activity_type:
            return response

        try:
            # Extract query params
            query_params = dict(request.GET.items()) if request.GET else {}

            # Create activity log
            ActivityLog.objects.create(
                user=request.user,
                activity_type=activity_type,
                path=request.path,
                query_params=query_params,
                timestamp=timezone.now(),
                duration_ms=duration_ms,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                session_key=request.session.session_key if hasattr(request, 'session') else '',
                metadata={
                    'method': request.method,
                    'status_code': response.status_code,
                }
            )
        except Exception as e:
            # Don't break the request if logging fails
            SystemEvent.log_event(
                level='ERROR',
                category='SYSTEM',
                event_name='Activity Logging Failed',
                message=f'Failed to log activity: {str(e)}',
                user=request.user,
                request=request,
                exception=e
            )

        return response

    def _determine_activity_type(self, request):
        """Determine the type of activity based on the request"""
        path = request.path.lower()

        # API calls
        if path.startswith('/api/'):
            return 'API_CALL'

        # Downloads/Exports
        if 'export' in path or 'download' in path:
            return 'DOWNLOAD'

        # Uploads
        if request.method == 'POST' and request.FILES:
            return 'UPLOAD'

        # Search
        if 'search' in request.GET or 'q' in request.GET:
            return 'SEARCH'

        # Filter
        if len(request.GET) > 0 and request.method == 'GET':
            return 'FILTER'

        # Regular page view
        if request.method == 'GET':
            return 'PAGE_VIEW'

        return None

    def _get_client_ip(self, request):
        """Extract the client's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditTrailMiddleware(MiddlewareMixin):
    """
    Middleware to capture audit information for all requests

    Stores request context for use in model signals
    """

    def process_request(self, request):
        """Store request context in thread-local storage"""
        # Store current request for access in signals
        request._audit_context = {
            'user': getattr(request, 'user', None),
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
            'session_key': request.session.session_key if hasattr(request, 'session') else '',
            'timestamp': timezone.now(),
        }
        return None

    def _get_client_ip(self, request):
        """Extract the client's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ErrorMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor and log errors

    Captures exceptions and logs them to SystemEvent
    """

    def process_exception(self, request, exception):
        """Log exceptions to SystemEvent"""
        try:
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None

            SystemEvent.log_event(
                level='ERROR',
                category='SYSTEM',
                event_name='Unhandled Exception',
                message=f'Unhandled exception in {request.path}',
                user=user,
                request=request,
                exception=exception
            )
        except Exception:
            # Don't break if error logging fails
            pass

        # Return None to allow Django's default exception handling
        return None


class RequestTimingMiddleware(MiddlewareMixin):
    """
    Middleware to track request timing and performance

    Logs slow requests to SystemEvent for performance monitoring
    """

    SLOW_REQUEST_THRESHOLD_MS = 1000  # 1 second

    def process_request(self, request):
        """Mark the start time of the request"""
        request._start_time = time.time()
        return None

    def process_response(self, request, response):
        """Check request duration and log if slow"""
        if not hasattr(request, '_start_time'):
            return response

        duration = time.time() - request._start_time
        duration_ms = int(duration * 1000)

        # Log slow requests
        if duration_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            try:
                user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None

                SystemEvent.log_event(
                    level='WARNING',
                    category='SYSTEM',
                    event_name='Slow Request',
                    message=f'Request to {request.path} took {duration_ms}ms',
                    user=user,
                    request=request,
                    duration_ms=duration_ms,
                    method=request.method,
                    status_code=response.status_code
                )
            except Exception:
                pass

        # Add timing header to response
        response['X-Request-Duration'] = f'{duration_ms}ms'

        return response


# ============================================================================
# SIGNAL HANDLERS FOR AUDIT LOGGING
# ============================================================================

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login events"""
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    AuditLog.log_action(
        user=user,
        action='LOGIN',
        message=f'User {user.username} logged in',
        ip_address=ip_address,
        user_agent=user_agent
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout events"""
    if user:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        AuditLog.log_action(
            user=user,
            action='LOGOUT',
            message=f'User {user.username} logged out',
            ip_address=ip_address,
            user_agent=user_agent
        )


def auto_audit_log(sender, instance, created, **kwargs):
    """
    Generic signal handler to automatically log model changes

    Usage:
        In your model's ready() method:
        post_save.connect(auto_audit_log, sender=YourModel)
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Skip for User model to avoid recursion
    if isinstance(instance, User):
        return

    # Get audit context from current request if available
    try:
        from threading import current_thread
        for attr in dir(current_thread()):
            if 'request' in attr.lower():
                request = getattr(current_thread(), attr, None)
                if hasattr(request, '_audit_context'):
                    context = request._audit_context
                    break
        else:
            context = {}
    except Exception:
        context = {}

    action = 'CREATE' if created else 'UPDATE'

    AuditLog.log_action(
        user=context.get('user'),
        action=action,
        obj=instance,
        message=f'{action.title()} {instance.__class__.__name__}',
        ip_address=context.get('ip_address'),
        user_agent=context.get('user_agent'),
    )


def auto_audit_delete(sender, instance, **kwargs):
    """
    Generic signal handler to automatically log model deletions

    Usage:
        In your model's ready() method:
        pre_delete.connect(auto_audit_delete, sender=YourModel)
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Skip for User model
    if isinstance(instance, User):
        return

    # Get audit context from current request if available
    try:
        from threading import current_thread
        for attr in dir(current_thread()):
            if 'request' in attr.lower():
                request = getattr(current_thread(), attr, None)
                if hasattr(request, '_audit_context'):
                    context = request._audit_context
                    break
        else:
            context = {}
    except Exception:
        context = {}

    AuditLog.log_action(
        user=context.get('user'),
        action='DELETE',
        obj=instance,
        message=f'Delete {instance.__class__.__name__}',
        ip_address=context.get('ip_address'),
        user_agent=context.get('user_agent'),
    )
