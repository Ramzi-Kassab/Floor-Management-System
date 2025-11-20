"""
Middleware for automatic analytics tracking
"""
from django.utils import timezone
from django.urls import resolve
from floor_app.operations.analytics.models import PageView, UserSession, ErrorLog
from floor_app.operations.analytics.utils import get_client_ip, get_module_from_url
import time


# Thread-local storage for current user
_thread_locals = {}


def get_current_user():
    """Get the current user from thread-local storage"""
    return _thread_locals.get('user', None)


def get_current_request():
    """Get the current request from thread-local storage"""
    return _thread_locals.get('request', None)


class AnalyticsMiddleware:
    """
    Middleware to automatically track page views and user activities
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request and user in thread-local storage for access in signals
        _thread_locals['request'] = request
        _thread_locals['user'] = getattr(request, 'user', None)

        # Start timer for page load time
        start_time = time.time()

        # Process the request
        response = self.get_response(request)

        # Calculate load time
        load_time_ms = int((time.time() - start_time) * 1000)

        # Track page view (only for authenticated users and successful responses)
        if hasattr(request, 'user') and request.user.is_authenticated:
            if response.status_code < 400:  # Only track successful requests
                self.track_page_view(request, load_time_ms)

            # Update session last activity
            self.update_session_activity(request)

        # Clean up thread-local storage
        _thread_locals.pop('request', None)
        _thread_locals.pop('user', None)

        return response

    def track_page_view(self, request, load_time_ms):
        """Track a page view"""
        try:
            # Get session
            session = None
            session_id = request.session.get('analytics_session_id')
            if session_id:
                try:
                    session = UserSession.objects.get(id=session_id)
                except UserSession.DoesNotExist:
                    pass

            # Get URL information
            url = request.path
            url_name = ''
            module = ''

            try:
                resolved = resolve(request.path)
                url_name = resolved.url_name or ''
                module = get_module_from_url(url_name)
                if not module and resolved.namespace:
                    module = resolved.namespace
            except:
                pass

            # Get query parameters
            query_params = dict(request.GET.items()) if request.GET else {}

            # Get referrer
            referrer = request.META.get('HTTP_REFERER', '')

            # Create page view record
            PageView.objects.create(
                session=session,
                user=request.user,
                url=url[:500],  # Limit length
                url_name=url_name[:100],
                module=module[:50],
                view_name=resolved.view_name[:100] if resolved else '',
                referrer=referrer[:500],
                load_time_ms=load_time_ms,
                query_params=query_params
            )

        except Exception as e:
            # Don't let tracking errors break the application
            print(f"Error tracking page view: {e}")

    def update_session_activity(self, request):
        """Update last activity time for the session"""
        try:
            session_id = request.session.get('analytics_session_id')
            if session_id:
                UserSession.objects.filter(id=session_id).update(
                    last_activity=timezone.now()
                )
        except Exception as e:
            print(f"Error updating session activity: {e}")

    def process_exception(self, request, exception):
        """Track exceptions"""
        try:
            # Get session and user
            session = None
            user = None

            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
                session_id = request.session.get('analytics_session_id')
                if session_id:
                    try:
                        session = UserSession.objects.get(id=session_id)
                    except UserSession.DoesNotExist:
                        pass

            # Get URL information
            url = request.path
            module = ''
            view_name = ''

            try:
                resolved = resolve(request.path)
                url_name = resolved.url_name or ''
                view_name = resolved.view_name or ''
                module = get_module_from_url(url_name)
                if not module and resolved.namespace:
                    module = resolved.namespace
            except:
                pass

            # Get error information
            import traceback
            error_type = exception.__class__.__name__
            error_message = str(exception)
            traceback_str = traceback.format_exc()

            # Get request data (safe subset)
            request_data = {
                'method': request.method,
                'path': request.path,
                'GET': dict(request.GET.items()),
            }

            # Don't log sensitive POST data by default
            # You can customize this based on your security requirements

            # Log error
            ErrorLog.objects.create(
                session=session,
                user=user,
                severity='error',
                error_type=error_type[:100],
                error_message=error_message,
                url=url[:500],
                module=module[:50],
                view_name=view_name[:100],
                traceback=traceback_str,
                request_data=request_data,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:1000],
                ip_address=get_client_ip(request)
            )

        except Exception as e:
            # Don't let error tracking errors break the application
            print(f"Error logging exception: {e}")

        # Return None to continue with default exception handling
        return None
