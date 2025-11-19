"""
Custom template tags and filters for Retrieval System
"""

from django import template
from django.contrib.contenttypes.models import ContentType
from floor_app.operations.retrieval.services import RetrievalService

register = template.Library()


@register.filter
def content_type_id(obj):
    """
    Get ContentType ID for an object.

    Usage:
        {% load retrieval_tags %}
        <a href="{% url 'retrieval:create_request' object|content_type_id object.pk %}">
            Request Retrieval
        </a>
    """
    if obj is None:
        return None
    ct = ContentType.objects.get_for_model(obj)
    return ct.id


@register.simple_tag
def employee_accuracy(employee, period='month'):
    """
    Get employee accuracy metrics for a period.

    Usage:
        {% load retrieval_tags %}
        {% employee_accuracy request.user 'month' as accuracy %}
        <p>Accuracy: {{ accuracy.accuracy_rate }}%</p>
    """
    return RetrievalService.calculate_employee_accuracy(employee, period)


@register.simple_tag
def supervisor_pending_count(supervisor):
    """
    Get count of pending retrieval requests for a supervisor.

    Usage:
        {% load retrieval_tags %}
        {% supervisor_pending_count request.user as pending_count %}
        <span class="badge">{{ pending_count }}</span>
    """
    return RetrievalService.get_supervisor_pending_count(supervisor)


@register.filter
def can_retrieve(obj):
    """
    Check if object can be retrieved.

    Usage:
        {% load retrieval_tags %}
        {% if object|can_retrieve %}
            <button>Request Retrieval</button>
        {% endif %}
    """
    if not hasattr(obj, 'can_be_retrieved'):
        return False
    can_retrieve, reasons = obj.can_be_retrieved()
    return can_retrieve


@register.filter
def retrieval_status_icon(status):
    """
    Get Bootstrap icon class for retrieval status.

    Usage:
        {% load retrieval_tags %}
        <i class="bi {{ request.status|retrieval_status_icon }}"></i>
    """
    icons = {
        'PENDING': 'bi-clock-history',
        'AUTO_APPROVED': 'bi-check-circle-fill',
        'APPROVED': 'bi-check-circle',
        'REJECTED': 'bi-x-circle-fill',
        'COMPLETED': 'bi-check-all',
        'CANCELLED': 'bi-x-octagon',
    }
    return icons.get(status, 'bi-question-circle')


@register.filter
def retrieval_status_color(status):
    """
    Get color class for retrieval status.

    Usage:
        {% load retrieval_tags %}
        <span class="text-{{ request.status|retrieval_status_color }}">
            {{ request.get_status_display }}
        </span>
    """
    colors = {
        'PENDING': 'warning',
        'AUTO_APPROVED': 'success',
        'APPROVED': 'success',
        'REJECTED': 'danger',
        'COMPLETED': 'primary',
        'CANCELLED': 'secondary',
    }
    return colors.get(status, 'secondary')


@register.filter
def accuracy_color(accuracy_rate):
    """
    Get color class based on accuracy rate.

    Usage:
        {% load retrieval_tags %}
        <span class="text-{{ metrics.accuracy_rate|accuracy_color }}">
            {{ metrics.accuracy_rate }}%
        </span>
    """
    rate = float(accuracy_rate)
    if rate >= 95:
        return 'success'
    elif rate >= 90:
        return 'warning'
    else:
        return 'danger'


@register.inclusion_tag('retrieval/widgets/retrieval_button.html')
def retrieval_button(obj, user, button_class='btn btn-warning btn-sm'):
    """
    Render a retrieval request button for an object.

    Usage:
        {% load retrieval_tags %}
        {% retrieval_button object request.user %}
    """
    can_retrieve = False
    reasons = []

    if hasattr(obj, 'can_be_retrieved'):
        can_retrieve, reasons = obj.can_be_retrieved()

    ct = ContentType.objects.get_for_model(obj)

    return {
        'object': obj,
        'can_retrieve': can_retrieve,
        'reasons': reasons,
        'content_type_id': ct.id,
        'button_class': button_class
    }


@register.inclusion_tag('retrieval/widgets/accuracy_badge.html')
def accuracy_badge(employee, period='month', size='normal'):
    """
    Render an accuracy badge for an employee.

    Usage:
        {% load retrieval_tags %}
        {% accuracy_badge request.user 'month' 'small' %}
    """
    metrics = RetrievalService.calculate_employee_accuracy(employee, period)

    return {
        'employee': employee,
        'metrics': metrics,
        'period': period,
        'size': size
    }


@register.filter
def minutes_elapsed(time_elapsed):
    """
    Convert timedelta to minutes.

    Usage:
        {% load retrieval_tags %}
        {{ request.time_elapsed|minutes_elapsed }} minutes
    """
    if not time_elapsed:
        return 0
    return int(time_elapsed.total_seconds() / 60)


@register.filter
def dict_get(dictionary, key):
    """
    Get value from dictionary by key.

    Usage:
        {% load retrieval_tags %}
        {{ employee_metrics|dict_get:employee.id }}
    """
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)
