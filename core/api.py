"""
REST API Framework for Floor Management System.

Features:
- RESTful API helpers
- API versioning
- Rate limiting
- API key authentication
- Response formatting
- Pagination helpers
"""

import time
import hashlib
from functools import wraps
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage

User = get_user_model()


class APIResponse:
    """Standardized API response formatting."""

    @staticmethod
    def success(data=None, message=None, status=200, meta=None):
        """Return successful API response."""
        response = {
            'success': True,
            'status': status,
        }

        if message:
            response['message'] = message

        if data is not None:
            response['data'] = data

        if meta:
            response['meta'] = meta

        return JsonResponse(response, status=status)

    @staticmethod
    def error(message, status=400, errors=None, code=None):
        """Return error API response."""
        response = {
            'success': False,
            'status': status,
            'message': message,
        }

        if errors:
            response['errors'] = errors

        if code:
            response['code'] = code

        return JsonResponse(response, status=status)

    @staticmethod
    def paginated(queryset, page=1, per_page=20, serializer=None):
        """Return paginated API response."""
        paginator = Paginator(queryset, per_page)

        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # Serialize data if serializer provided
        if serializer:
            data = [serializer(item) for item in page_obj.object_list]
        else:
            data = list(page_obj.object_list.values())

        meta = {
            'pagination': {
                'page': page_obj.number,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        }

        return APIResponse.success(data=data, meta=meta)


class RateLimiter:
    """
    API rate limiting.

    Limits requests per time window using cache backend.
    """

    @staticmethod
    def get_rate_limit_key(identifier, endpoint):
        """Generate cache key for rate limiting."""
        return f'rate_limit:{endpoint}:{identifier}'

    @staticmethod
    def is_rate_limited(identifier, endpoint, max_requests=60, window=60):
        """
        Check if identifier has exceeded rate limit.

        Args:
            identifier: User ID, IP address, or API key
            endpoint: API endpoint being accessed
            max_requests: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            tuple: (is_limited, remaining, reset_time)
        """
        key = RateLimiter.get_rate_limit_key(identifier, endpoint)

        # Get current request count
        current = cache.get(key, {
            'count': 0,
            'reset': time.time() + window
        })

        # Check if window has expired
        if time.time() > current['reset']:
            current = {
                'count': 0,
                'reset': time.time() + window
            }

        # Increment count
        current['count'] += 1
        cache.set(key, current, window)

        # Check if limit exceeded
        is_limited = current['count'] > max_requests
        remaining = max(0, max_requests - current['count'])

        return is_limited, remaining, int(current['reset'])

    @staticmethod
    def get_remaining_requests(identifier, endpoint, max_requests=60):
        """Get remaining requests in current window."""
        key = RateLimiter.get_rate_limit_key(identifier, endpoint)
        current = cache.get(key, {'count': 0})
        return max(0, max_requests - current['count'])


def rate_limit(max_requests=60, window=60, identifier_func=None):
    """
    Decorator for rate limiting API endpoints.

    Args:
        max_requests: Maximum requests allowed in window
        window: Time window in seconds
        identifier_func: Function to get identifier from request (default: user ID or IP)

    Usage:
        @rate_limit(max_requests=100, window=60)
        def my_api_view(request):
            pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Get identifier
            if identifier_func:
                identifier = identifier_func(request)
            elif request.user.is_authenticated:
                identifier = f'user:{request.user.id}'
            else:
                # Use IP address
                from core.security import get_client_ip
                identifier = f'ip:{get_client_ip(request)}'

            # Get endpoint name
            endpoint = func.__name__

            # Check rate limit
            is_limited, remaining, reset_time = RateLimiter.is_rate_limited(
                identifier, endpoint, max_requests, window
            )

            # Add rate limit headers
            response = None
            if is_limited:
                response = APIResponse.error(
                    message='Rate limit exceeded',
                    status=429,
                    code='RATE_LIMIT_EXCEEDED'
                )
            else:
                response = func(request, *args, **kwargs)

            # Add rate limit headers to response
            if hasattr(response, '__setitem__'):
                response['X-RateLimit-Limit'] = str(max_requests)
                response['X-RateLimit-Remaining'] = str(remaining)
                response['X-RateLimit-Reset'] = str(reset_time)

            return response

        return wrapper

    return decorator


class APIKeyAuth:
    """
    API Key authentication.

    Features:
    - Generate API keys
    - Validate API keys
    - Track API key usage
    """

    @staticmethod
    def generate_key(user, name='Default'):
        """
        Generate a new API key for user.

        Returns:
            tuple: (api_key, api_secret)
        """
        import secrets

        # Generate key and secret
        api_key = f'fms_{secrets.token_urlsafe(24)}'
        api_secret = secrets.token_urlsafe(32)

        # Hash secret for storage
        secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()

        # Store in cache or database
        cache.set(
            f'api_key:{api_key}',
            {
                'user_id': user.id,
                'name': name,
                'secret_hash': secret_hash,
                'created_at': time.time()
            },
            timeout=None  # Persistent
        )

        return api_key, api_secret

    @staticmethod
    def validate_key(api_key, api_secret):
        """
        Validate API key and secret.

        Returns:
            User object if valid, None otherwise
        """
        # Get key data
        key_data = cache.get(f'api_key:{api_key}')

        if not key_data:
            return None

        # Verify secret
        secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()

        if secret_hash != key_data['secret_hash']:
            return None

        # Get user
        try:
            user = User.objects.get(id=key_data['user_id'])
            return user if user.is_active else None
        except User.DoesNotExist:
            return None

    @staticmethod
    def revoke_key(api_key):
        """Revoke an API key."""
        cache.delete(f'api_key:{api_key}')

    @staticmethod
    def get_user_keys(user):
        """Get all API keys for a user (limited information)."""
        # This would require database storage for full implementation
        # For now, we can't list all keys from cache
        # In production, store API keys in database
        pass


def require_api_key(func):
    """
    Decorator to require API key authentication.

    Usage:
        @require_api_key
        def my_api_view(request):
            # request.api_user will be set
            pass
    """

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Get API key from header
        api_key = request.META.get('HTTP_X_API_KEY', '')
        api_secret = request.META.get('HTTP_X_API_SECRET', '')

        if not api_key or not api_secret:
            return APIResponse.error(
                message='API key and secret required',
                status=401,
                code='MISSING_API_CREDENTIALS'
            )

        # Validate API key
        user = APIKeyAuth.validate_key(api_key, api_secret)

        if not user:
            return APIResponse.error(
                message='Invalid API credentials',
                status=401,
                code='INVALID_API_CREDENTIALS'
            )

        # Attach user to request
        request.api_user = user

        return func(request, *args, **kwargs)

    return wrapper


class APIVersioning:
    """
    API versioning support.

    Supports version extraction from:
    - URL path (/api/v1/resource/)
    - Header (X-API-Version)
    - Query parameter (?version=1)
    """

    DEFAULT_VERSION = '1.0'
    SUPPORTED_VERSIONS = ['1.0', '2.0']

    @staticmethod
    def get_version(request):
        """Extract API version from request."""
        # Try header
        version = request.META.get('HTTP_X_API_VERSION')
        if version:
            return version

        # Try query parameter
        version = request.GET.get('version')
        if version:
            return version

        # Try URL path
        path_parts = request.path.split('/')
        for part in path_parts:
            if part.startswith('v') and part[1:].replace('.', '').isdigit():
                return part[1:]

        # Default version
        return APIVersioning.DEFAULT_VERSION

    @staticmethod
    def is_supported(version):
        """Check if version is supported."""
        return version in APIVersioning.SUPPORTED_VERSIONS


def versioned_api(supported_versions=None):
    """
    Decorator for versioned API endpoints.

    Usage:
        @versioned_api(supported_versions=['1.0', '2.0'])
        def my_api_view(request, version):
            if version == '1.0':
                # V1 logic
            elif version == '2.0':
                # V2 logic
    """
    if supported_versions is None:
        supported_versions = APIVersioning.SUPPORTED_VERSIONS

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            version = APIVersioning.get_version(request)

            if version not in supported_versions:
                return APIResponse.error(
                    message=f'API version {version} not supported',
                    status=400,
                    code='UNSUPPORTED_VERSION'
                )

            # Pass version to function
            kwargs['api_version'] = version

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def api_endpoint(method='GET', rate_limit_config=None, require_auth=True, api_key_auth=False):
    """
    Combined decorator for API endpoints.

    Args:
        method: HTTP method(s) allowed (string or list)
        rate_limit_config: Dict with 'max_requests' and 'window'
        require_auth: Whether to require user authentication
        api_key_auth: Whether to use API key authentication

    Usage:
        @api_endpoint(
            method=['GET', 'POST'],
            rate_limit_config={'max_requests': 100, 'window': 60},
            require_auth=True
        )
        def my_api_view(request):
            pass
    """

    def decorator(func):
        wrapped_func = func

        # Apply API key auth if requested
        if api_key_auth:
            wrapped_func = require_api_key(wrapped_func)

        # Apply rate limiting if configured
        if rate_limit_config:
            wrapped_func = rate_limit(**rate_limit_config)(wrapped_func)

        @wraps(wrapped_func)
        def wrapper(request, *args, **kwargs):
            # Check HTTP method
            methods = [method] if isinstance(method, str) else method
            if request.method not in methods:
                return APIResponse.error(
                    message=f'Method {request.method} not allowed',
                    status=405,
                    code='METHOD_NOT_ALLOWED'
                )

            # Check authentication
            if require_auth and not api_key_auth and not request.user.is_authenticated:
                return APIResponse.error(
                    message='Authentication required',
                    status=401,
                    code='AUTHENTICATION_REQUIRED'
                )

            return wrapped_func(request, *args, **kwargs)

        return wrapper

    return decorator
