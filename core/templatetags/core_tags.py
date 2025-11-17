"""
Template tags for core app functionality.
Provides utility filters for data tables and templates.
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_attr(obj, attr):
    """
    Get attribute from object, supports nested attributes with dot notation.
    Usage: {{ item|get_attr:"user.username" }}
    """
    if not attr:
        return None

    attrs = attr.split('.')
    value = obj

    for a in attrs:
        if hasattr(value, a):
            value = getattr(value, a)
        elif isinstance(value, dict):
            value = value.get(a, None)
        else:
            return None

        # Handle callable attributes (methods)
        if callable(value):
            try:
                value = value()
            except Exception:
                return None

    return value


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key.
    Usage: {{ request.GET|get_item:"status" }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''


@register.filter
def format_currency(value, currency='SAR'):
    """
    Format value as currency.
    Usage: {{ amount|format_currency:"USD" }}
    """
    try:
        value = float(value)
        return f"{value:,.2f} {currency}"
    except (ValueError, TypeError):
        return value


@register.filter
def percentage(value, total):
    """
    Calculate percentage.
    Usage: {{ part|percentage:total }}
    """
    try:
        if total == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.simple_tag
def theme_class(theme):
    """
    Return CSS class for theme.
    Usage: {% theme_class theme %}
    """
    theme_classes = {
        'light': 'theme-light',
        'dark': 'theme-dark',
        'high_contrast': 'theme-high-contrast',
    }
    return theme_classes.get(theme, 'theme-light')


@register.simple_tag
def font_size_class(size):
    """
    Return CSS class for font size.
    Usage: {% font_size_class font_size %}
    """
    size_classes = {
        'small': 'ui-font-small',
        'normal': 'ui-font-normal',
        'large': 'ui-font-large',
    }
    return size_classes.get(size, 'ui-font-normal')


@register.simple_tag
def density_class(density):
    """
    Return CSS class for table density.
    Usage: {% density_class table_density %}
    """
    density_classes = {
        'compact': 'table-density-compact',
        'normal': 'table-density-normal',
        'relaxed': 'table-density-relaxed',
    }
    return density_classes.get(density, 'table-density-normal')


@register.inclusion_tag('core/partials/erp_badge.html')
def erp_reference_badge(obj):
    """
    Display ERP references for an object as badges.
    Usage: {% erp_reference_badge item %}
    """
    from django.contrib.contenttypes.models import ContentType
    from core.models import ERPReference

    content_type = ContentType.objects.get_for_model(obj)
    references = ERPReference.objects.filter(
        content_type=content_type,
        object_id=obj.pk
    ).select_related('document_type')

    return {
        'references': references,
        'has_references': references.exists(),
    }


@register.filter
def status_badge_class(status):
    """
    Return Bootstrap badge class for status.
    Usage: {{ status|status_badge_class }}
    """
    status_classes = {
        'active': 'bg-success',
        'inactive': 'bg-secondary',
        'pending': 'bg-warning',
        'approved': 'bg-success',
        'rejected': 'bg-danger',
        'draft': 'bg-info',
        'submitted': 'bg-primary',
        'reviewed': 'bg-info',
        'error': 'bg-danger',
        'synced': 'bg-success',
        'manual': 'bg-secondary',
    }
    return status_classes.get(str(status).lower(), 'bg-secondary')


@register.filter
def truncate_middle(value, length=50):
    """
    Truncate string in the middle if too long.
    Usage: {{ long_string|truncate_middle:30 }}
    """
    value = str(value)
    if len(value) <= length:
        return value

    half = (length - 3) // 2
    return f"{value[:half]}...{value[-half:]}"
