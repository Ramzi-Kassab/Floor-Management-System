"""
Custom Template Tags and Filters for HR Module

Usage in templates:
    {% load hr_tags %}
    {{ employee|employee_status_badge }}
    {% employee_card employee %}
"""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from datetime import date, timedelta

register = template.Library()


# ============================================================================
# FILTERS
# ============================================================================

@register.filter
def employee_status_badge(employee):
    """
    Display employee status as a colored badge

    Usage: {{ employee|employee_status_badge }}
    """
    status_colors = {
        'ACTIVE': 'success',
        'ON_LEAVE': 'warning',
        'TERMINATED': 'danger',
        'SUSPENDED': 'danger',
    }

    color = status_colors.get(employee.employment_status, 'secondary')
    status_display = employee.get_employment_status_display()

    return format_html(
        '<span class="badge bg-{}">{}</span>',
        color,
        status_display
    )


@register.filter
def leave_status_badge(leave_request):
    """
    Display leave request status as a colored badge

    Usage: {{ leave_request|leave_status_badge }}
    """
    status_colors = {
        'PENDING': 'warning',
        'APPROVED': 'success',
        'REJECTED': 'danger',
        'CANCELLED': 'secondary',
    }

    color = status_colors.get(leave_request.status, 'secondary')
    status_display = leave_request.get_status_display()

    return format_html(
        '<span class="badge bg-{}">{}</span>',
        color,
        status_display
    )


@register.filter
def asset_status_badge(asset):
    """
    Display asset status as a colored badge

    Usage: {{ asset|asset_status_badge }}
    """
    status_colors = {
        'AVAILABLE': 'success',
        'ASSIGNED': 'primary',
        'MAINTENANCE': 'warning',
        'RETIRED': 'danger',
    }

    color = status_colors.get(asset.status, 'secondary')
    status_display = asset.get_status_display()

    return format_html(
        '<span class="badge bg-{}">{}</span>',
        color,
        status_display
    )


@register.filter
def service_duration(employee):
    """
    Calculate and display service duration

    Usage: {{ employee|service_duration }}
    """
    if not employee.hire_date:
        return '-'

    end_date = employee.termination_date or date.today()
    delta = end_date - employee.hire_date

    years = delta.days // 365
    months = (delta.days % 365) // 30

    if years > 0:
        return f"{years}y {months}m"
    elif months > 0:
        return f"{months}m"
    else:
        return f"{delta.days}d"


@register.filter
def days_until(target_date):
    """
    Calculate days until a target date

    Usage: {{ contract.end_date|days_until }}
    """
    if not target_date:
        return '-'

    if isinstance(target_date, str):
        return target_date

    today = date.today()
    delta = target_date - today

    if delta.days < 0:
        return format_html('<span class="text-danger">Expired</span>')
    elif delta.days == 0:
        return format_html('<span class="text-warning">Today</span>')
    elif delta.days <= 30:
        return format_html('<span class="text-warning">{} days</span>', delta.days)
    else:
        return f"{delta.days} days"


@register.filter
def leave_days_count(leave_request):
    """
    Calculate number of leave days

    Usage: {{ leave_request|leave_days_count }}
    """
    if not leave_request.start_date or not leave_request.end_date:
        return 0

    delta = leave_request.end_date - leave_request.start_date
    return delta.days + 1


@register.filter
def employee_initials(employee):
    """
    Get employee initials

    Usage: {{ employee|employee_initials }}
    """
    if not employee or not employee.person:
        return '??'

    first = employee.person.first_name[0] if employee.person.first_name else ''
    last = employee.person.last_name[0] if employee.person.last_name else ''

    return f"{first}{last}".upper()


@register.filter
def yes_no_badge(value):
    """
    Display boolean as Yes/No badge

    Usage: {{ contract.is_active|yes_no_badge }}
    """
    if value:
        return format_html('<span class="badge bg-success">Yes</span>')
    else:
        return format_html('<span class="badge bg-danger">No</span>')


# ============================================================================
# TAGS (INCLUSION TAGS)
# ============================================================================

@register.inclusion_tag('hr/tags/employee_card.html')
def employee_card(employee, show_details=True):
    """
    Render an employee card

    Usage: {% employee_card employee %}
    """
    return {
        'employee': employee,
        'show_details': show_details,
    }


@register.inclusion_tag('hr/tags/leave_request_card.html')
def leave_request_card(leave_request):
    """
    Render a leave request card

    Usage: {% leave_request_card leave_request %}
    """
    days = 0
    if leave_request.start_date and leave_request.end_date:
        days = (leave_request.end_date - leave_request.start_date).days + 1

    return {
        'leave_request': leave_request,
        'days': days,
    }


@register.inclusion_tag('hr/tags/department_stats.html')
def department_stats(department):
    """
    Render department statistics

    Usage: {% department_stats department %}
    """
    active_count = department.employee_set.filter(
        employment_status='ACTIVE'
    ).count()

    total_count = department.employee_set.count()

    return {
        'department': department,
        'active_count': active_count,
        'total_count': total_count,
    }


# ============================================================================
# SIMPLE TAGS
# ============================================================================

@register.simple_tag
def pending_leave_requests_count(employee):
    """
    Get count of pending leave requests for employee

    Usage: {% pending_leave_requests_count employee as count %}
    """
    return employee.leaverequest_set.filter(status='PENDING').count()


@register.simple_tag
def active_contracts_count(employee):
    """
    Get count of active contracts for employee

    Usage: {% active_contracts_count employee as count %}
    """
    return employee.contract_set.filter(is_active=True).count()


@register.simple_tag
def assigned_assets_count(employee):
    """
    Get count of assigned assets for employee

    Usage: {% assigned_assets_count employee as count %}
    """
    return employee.assetassignment_set.filter(
        returned_date__isnull=True
    ).count()


@register.simple_tag
def get_leave_balance(employee, leave_type, year=None):
    """
    Get leave balance for employee and leave type

    Usage: {% get_leave_balance employee leave_type as balance %}
    """
    if year is None:
        year = date.today().year

    # This would require a LeaveBalance model
    # For now, return default
    return leave_type.days_per_year if leave_type else 0


# ============================================================================
# ASSIGNMENT TAGS
# ============================================================================

@register.simple_tag
def is_manager_of(manager, employee):
    """
    Check if manager is the reporting manager of employee

    Usage: {% is_manager_of manager employee as is_mgr %}
    """
    if not employee or not employee.report_to:
        return False

    return employee.report_to.pk == manager.pk


@register.simple_tag
def has_permission(user, perm_name):
    """
    Check if user has specific permission

    Usage: {% has_permission user 'hr.approve_leave' as can_approve %}
    """
    if not user or not user.is_authenticated:
        return False

    return user.has_perm(perm_name)


# ============================================================================
# UTILITY TAGS
# ============================================================================

@register.filter
def add_class(field, css_class):
    """
    Add CSS class to form field

    Usage: {{ form.field|add_class:"form-control" }}
    """
    return field.as_widget(attrs={'class': css_class})


@register.filter
def field_type(field):
    """
    Get field widget type

    Usage: {% if form.field|field_type == "CheckboxInput" %}
    """
    return field.field.widget.__class__.__name__


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Transform current query string

    Usage: {% query_transform page=2 %}
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()
