"""
HR Permission Decorators and Mixins

Provides decorators for enforcing RBAC in HR views.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def hr_permission_required(permission_codename):
    """
    Decorator that requires both login and specific HR permission.
    Redirects to login if not authenticated, raises 403 if no permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.has_perm(permission_codename):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this resource.')
                raise PermissionDenied
        return _wrapped_view
    return decorator


def hr_view_permission(view_func):
    """Decorator for views that require view permission on HR data."""
    return hr_permission_required('hr.view_hremployee')(view_func)


def hr_add_permission(view_func):
    """Decorator for views that require add permission on HR data."""
    return hr_permission_required('hr.add_hremployee')(view_func)


def hr_change_permission(view_func):
    """Decorator for views that require change permission on HR data."""
    return hr_permission_required('hr.change_hremployee')(view_func)


def hr_delete_permission(view_func):
    """Decorator for views that require delete permission on HR data."""
    return hr_permission_required('hr.delete_hremployee')(view_func)


def hr_manager_required(view_func):
    """
    Decorator for views that require HR Manager level access.
    Checks if user is in hr_managers group or has superuser access.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name='hr_managers').exists():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'This action requires HR Manager privileges.')
            raise PermissionDenied
    return _wrapped_view


def can_view_salary(view_func):
    """Decorator for views that require salary viewing permission."""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if (request.user.is_superuser or
            request.user.has_perm('hr.can_view_salaries') or
            request.user.groups.filter(name__in=['hr_managers', 'administrators']).exists()):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'You do not have permission to view salary information.')
            raise PermissionDenied
    return _wrapped_view


def own_profile_only(view_func):
    """
    Decorator for views where users can only access their own profile.
    Allows superusers and HR managers to bypass.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Superusers and HR managers can view all
        if (request.user.is_superuser or
            request.user.groups.filter(name__in=['hr_managers', 'hr_officers', 'administrators']).exists()):
            return view_func(request, *args, **kwargs)

        # Check if this is the user's own profile
        pk = kwargs.get('pk')
        if pk and hasattr(request.user, 'hr_employee'):
            if request.user.hr_employee.pk == pk:
                return view_func(request, *args, **kwargs)
            # Also check if viewing their own person record
            if hasattr(request.user.hr_employee, 'person'):
                if request.user.hr_employee.person.pk == pk:
                    return view_func(request, *args, **kwargs)

        messages.error(request, 'You can only access your own profile.')
        raise PermissionDenied

    return _wrapped_view
