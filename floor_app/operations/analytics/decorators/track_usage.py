"""
Usage Tracking Decorators

Decorators to manually track specific views, actions, or reports.

Use when you want to:
- Track specific events beyond page views
- Add custom metadata
- Track non-view functions
- Override automatic tracking
"""

from functools import wraps
from django.conf import settings
import time


def track_view(view_name=None, event_type='PAGE_VIEW', event_category='', metadata=None):
    """
    Decorator to track view usage.

    Usage:
        @track_view(view_name='job_card_detail', event_category='Production')
        def job_card_detail(request, job_card_id):
            ...

        @track_view(event_type='REPORT_VIEW', event_category='Inventory')
        def cutter_inventory_report(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()

            # Execute view
            response = func(request, *args, **kwargs)

            # Log event
            try:
                from floor_app.operations.analytics.models import AppEvent

                # Determine view name
                _view_name = view_name or func.__name__

                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)

                # Build metadata
                _metadata = metadata or {}
                _metadata.update({
                    'function': func.__name__,
                    'args': [str(arg) for arg in args],
                    'kwargs': {k: str(v) for k, v in kwargs.items()},
                })

                # Log
                AppEvent.log_event(
                    user=request.user if hasattr(request, 'user') else None,
                    event_type=event_type,
                    view_name=_view_name,
                    event_category=event_category,
                    request=request,
                    duration_ms=duration_ms,
                    metadata=_metadata,
                )
            except Exception:
                # Don't let logging errors break the view
                pass

            return response

        return wrapper
    return decorator


def track_report(report_name, category='Reports'):
    """
    Specific decorator for reports.

    Usage:
        @track_report('Cutter Inventory Report', category='Inventory')
        def cutter_inventory_report(request):
            ...
    """
    return track_view(
        view_name=report_name,
        event_type='REPORT_VIEW',
        event_category=category
    )


def track_export(export_name, format_field='format', category='Exports'):
    """
    Specific decorator for exports.

    Usage:
        @track_export('Job Card Export', format_field='format')
        def export_job_cards(request):
            format = request.GET.get('format', 'csv')
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()

            # Execute export
            response = func(request, *args, **kwargs)

            # Log event
            try:
                from floor_app.operations.analytics.models import AppEvent

                # Get export format
                export_format = request.GET.get(format_field, 'unknown')

                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)

                # Log
                AppEvent.log_event(
                    user=request.user if hasattr(request, 'user') else None,
                    event_type='EXPORT',
                    view_name=export_name,
                    event_category=category,
                    request=request,
                    duration_ms=duration_ms,
                    metadata={
                        'format': export_format,
                        'function': func.__name__,
                    },
                )
            except Exception:
                pass

            return response

        return wrapper
    return decorator


def track_action(action_name, event_category='', get_metadata=None):
    """
    Decorator for tracking specific actions (create, update, delete, etc.).

    Usage:
        @track_action('Create Job Card', event_category='Production')
        def create_job_card(request):
            ...

        @track_action('Approve Quotation', get_metadata=lambda req, result: {'quotation_id': result.id})
        def approve_quotation(request, quotation_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()

            # Execute action
            response = func(request, *args, **kwargs)

            # Log event
            try:
                from floor_app.operations.analytics.models import AppEvent

                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)

                # Build metadata
                _metadata = {}
                if get_metadata and callable(get_metadata):
                    try:
                        _metadata = get_metadata(request, response)
                    except Exception:
                        pass

                # Log
                AppEvent.log_event(
                    user=request.user if hasattr(request, 'user') else None,
                    event_type='ACTION',
                    view_name=action_name,
                    event_category=event_category,
                    request=request,
                    duration_ms=duration_ms,
                    metadata=_metadata,
                )
            except Exception:
                pass

            return response

        return wrapper
    return decorator


def track_search(search_name='search', query_param='q', event_category='Search'):
    """
    Decorator for tracking search queries.

    Usage:
        @track_search(search_name='Job Card Search', query_param='q')
        def search_job_cards(request):
            query = request.GET.get('q')
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()

            # Execute search
            response = func(request, *args, **kwargs)

            # Log event
            try:
                from floor_app.operations.analytics.models import AppEvent

                # Get search query
                query = request.GET.get(query_param, '')

                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)

                # Log
                AppEvent.log_event(
                    user=request.user if hasattr(request, 'user') else None,
                    event_type='SEARCH',
                    view_name=search_name,
                    event_category=event_category,
                    request=request,
                    duration_ms=duration_ms,
                    metadata={
                        'query': query,
                        'query_length': len(query),
                    },
                )
            except Exception:
                pass

            return response

        return wrapper
    return decorator


# Non-request decorators for tracking function calls

def track_function(function_name=None, event_category='System'):
    """
    Decorator to track function execution (non-view functions).

    Useful for tracking:
    - Background tasks
    - Management commands
    - API calls
    - Internal operations

    Usage:
        @track_function('refresh_inventory_summary', event_category='Inventory')
        def refresh_inventory_summary():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Execute function
            result = func(*args, **kwargs)

            # Log event
            try:
                from floor_app.operations.analytics.models import AppEvent

                # Determine function name
                _function_name = function_name or func.__name__

                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)

                # Log
                AppEvent.objects.create(
                    user=None,  # No user for system functions
                    event_type='ACTION',
                    view_name=_function_name,
                    event_category=event_category,
                    http_path=f'/system/{_function_name}',
                    http_method='SYSTEM',
                    timestamp=timezone.now(),
                    duration_ms=duration_ms,
                    metadata={
                        'function': func.__name__,
                        'module': func.__module__,
                    },
                )
            except Exception:
                pass

            return result

        return wrapper
    return decorator
