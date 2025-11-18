"""
Event Tracking Middleware

Automatically logs page views and requests to AppEvent model.

Configuration in settings.py:
MIDDLEWARE = [
    ...
    'floor_app.operations.analytics.middleware.event_tracker.EventTrackingMiddleware',
    ...
]

Control tracking with settings:
ANALYTICS_TRACKING_ENABLED = True  # Master switch
ANALYTICS_TRACK_ANONYMOUS = False  # Track anonymous users
ANALYTICS_EXCLUDED_PATHS = ['/admin/', '/static/', '/media/']  # Don't track these paths
ANALYTICS_ASYNC_LOGGING = True  # Use Celery for async logging (recommended)
"""

from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
import time
import logging

logger = logging.getLogger(__name__)


class EventTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track page views and requests.

    Logs to AppEvent model with request details.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'ANALYTICS_TRACKING_ENABLED', True)
        self.track_anonymous = getattr(settings, 'ANALYTICS_TRACK_ANONYMOUS', False)
        self.excluded_paths = getattr(settings, 'ANALYTICS_EXCLUDED_PATHS', [
            '/admin/',
            '/static/',
            '/media/',
            '/__debug__/',
            '/favicon.ico',
        ])
        self.async_logging = getattr(settings, 'ANALYTICS_ASYNC_LOGGING', False)

    def process_request(self, request):
        """Mark request start time."""
        request._analytics_start_time = time.time()

    def process_response(self, request, response):
        """Log event after response is ready."""
        if not self.enabled:
            return response

        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return response

        # Skip anonymous users if configured
        if not self.track_anonymous and (not hasattr(request, 'user') or not request.user.is_authenticated):
            return response

        # Calculate duration
        duration_ms = None
        if hasattr(request, '_analytics_start_time'):
            duration_ms = int((time.time() - request._analytics_start_time) * 1000)

        # Determine event type
        event_type = self._determine_event_type(request, response)

        # Get view name
        view_name = self._get_view_name(request)

        # Get category
        event_category = self._get_category_from_path(request.path)

        # Log event
        try:
            if self.async_logging:
                # Use Celery task for async logging
                self._log_event_async(
                    user=request.user if request.user.is_authenticated else None,
                    event_type=event_type,
                    view_name=view_name,
                    event_category=event_category,
                    request=request,
                    duration_ms=duration_ms,
                )
            else:
                # Synchronous logging
                self._log_event_sync(
                    user=request.user if request.user.is_authenticated else None,
                    event_type=event_type,
                    view_name=view_name,
                    event_category=event_category,
                    request=request,
                    duration_ms=duration_ms,
                )
        except Exception as e:
            # Don't let logging errors break the response
            logger.error(f"Error logging analytics event: {e}")

        return response

    def _determine_event_type(self, request, response):
        """Determine event type based on request and response."""
        if request.method == 'GET':
            # Check if it's a report/export
            if 'export' in request.path.lower() or request.GET.get('export'):
                return 'EXPORT'
            elif 'report' in request.path.lower():
                return 'REPORT_VIEW'
            elif 'search' in request.path.lower() or request.GET.get('q'):
                return 'SEARCH'
            else:
                return 'PAGE_VIEW'
        elif request.method == 'POST':
            return 'ACTION'
        elif request.method in ['PUT', 'PATCH']:
            return 'UPDATE'
        elif request.method == 'DELETE':
            return 'DELETE'
        else:
            return 'CUSTOM'

    def _get_view_name(self, request):
        """Extract view name from request."""
        # Try to get from URL resolver
        if hasattr(request, 'resolver_match') and request.resolver_match:
            view_name = request.resolver_match.view_name
            if view_name:
                return view_name

        # Fall back to path
        path = request.path.strip('/')
        if not path:
            return 'home'

        # Clean up path for view name
        return path.replace('/', '_')[:200]

    def _get_category_from_path(self, path):
        """Infer category from URL path."""
        path_lower = path.lower()

        if 'inventory' in path_lower or 'cutter' in path_lower or 'stock' in path_lower:
            return 'Inventory'
        elif 'production' in path_lower or 'job' in path_lower or 'jobcard' in path_lower:
            return 'Production'
        elif 'planning' in path_lower or 'schedule' in path_lower:
            return 'Planning'
        elif 'quality' in path_lower or 'inspection' in path_lower:
            return 'Quality'
        elif 'hr' in path_lower or 'employee' in path_lower:
            return 'HR'
        elif 'maintenance' in path_lower:
            return 'Maintenance'
        elif 'analytics' in path_lower or 'report' in path_lower:
            return 'Analytics'
        else:
            return ''

    def _log_event_sync(self, user, event_type, view_name, event_category, request, duration_ms):
        """Log event synchronously."""
        from floor_app.operations.analytics.models import AppEvent

        AppEvent.log_event(
            user=user,
            event_type=event_type,
            view_name=view_name,
            event_category=event_category,
            request=request,
            duration_ms=duration_ms,
        )

    def _log_event_async(self, user, event_type, view_name, event_category, request, duration_ms):
        """Log event asynchronously via Celery."""
        try:
            from floor_app.operations.analytics.tasks import log_app_event_task

            log_app_event_task.delay(
                user_id=user.id if user else None,
                event_type=event_type,
                view_name=view_name,
                event_category=event_category,
                http_path=request.path,
                http_method=request.method,
                query_string=request.META.get('QUERY_STRING', ''),
                client_ip=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                session_key=request.session.session_key if hasattr(request, 'session') else '',
                duration_ms=duration_ms,
            )
        except ImportError:
            # Celery not available, fall back to sync
            self._log_event_sync(user, event_type, view_name, event_category, request, duration_ms)

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
