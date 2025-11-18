"""
Security middleware for the Floor Management System.

Middleware classes:
- SessionActivityMiddleware: Track session activity
- LoginAttemptMiddleware: Track and limit login attempts
- IPWhitelistMiddleware: Enforce IP whitelist
- SecurityHeadersMiddleware: Add security headers to responses
"""

from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .security import (
    SessionManager,
    LoginAttemptTracker,
    IPWhitelist,
    get_client_ip
)


class SessionActivityMiddleware:
    """
    Track user session activity.

    Updates last_activity timestamp on each request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Record session activity before processing request
        if request.user.is_authenticated:
            SessionManager.record_session_activity(request)

        response = self.get_response(request)
        return response


class IPWhitelistMiddleware:
    """
    Enforce IP whitelist for admin and sensitive areas.

    Can be configured to apply globally or to specific URL patterns.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # URL patterns to protect (can be configured in settings)
        from django.conf import settings
        self.protected_paths = getattr(settings, 'IP_WHITELIST_PATHS', [
            '/admin/',
            '/core/system/',
        ])

    def __call__(self, request):
        # Check if path is protected
        is_protected = any(request.path.startswith(path) for path in self.protected_paths)

        if is_protected:
            client_ip = get_client_ip(request)

            # Bypass for superusers (optional)
            if request.user.is_authenticated and request.user.is_superuser:
                pass  # Allow access
            elif not IPWhitelist.is_whitelisted(client_ip):
                return HttpResponseForbidden(
                    "Access denied: Your IP address is not authorized to access this resource."
                )

        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """
    Add security headers to all responses.

    Headers added:
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security (if HTTPS)
    - Content-Security-Policy
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking
        response['X-Frame-Options'] = 'SAMEORIGIN'

        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'

        # HSTS (only over HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )

        return response


# Signal receivers for login tracking
@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """Log successful login attempts."""
    ip_address = get_client_ip(request)
    LoginAttemptTracker.record_attempt(user.username, ip_address, success=True)
    LoginAttemptTracker.clear_attempts(username=user.username, ip_address=ip_address)

    # Log to activity log
    from .notification_utils import log_activity
    log_activity(
        user=user,
        action='LOGIN',
        description=f'User logged in successfully from {ip_address}',
        extra_data={
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500]
        },
        request=request
    )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempts."""
    username = credentials.get('username', 'unknown')
    ip_address = get_client_ip(request)

    LoginAttemptTracker.record_attempt(username, ip_address, success=False)

    # Log security event
    from .notification_utils import log_activity
    log_activity(
        user=None,
        action='LOGIN_FAILED',
        description=f'Failed login attempt for username "{username}" from {ip_address}',
        extra_data={
            'username': username,
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500]
        }
    )
