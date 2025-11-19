"""
Celery Tasks for Analytics

Async task processing for:
- Event logging
- Summary generation
- Rule execution
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def log_app_event_task(user_id, event_type, view_name, event_category='',
                       http_path='', http_method='GET', query_string='',
                       client_ip=None, user_agent='', session_key='',
                       duration_ms=None, metadata=None):
    """
    Async task to log app event.

    Called from EventTrackingMiddleware when ANALYTICS_ASYNC_LOGGING=True.
    """
    try:
        from floor_app.operations.analytics.models import AppEvent
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Get user
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass

        # Create event
        AppEvent.objects.create(
            user=user,
            event_type=event_type,
            view_name=view_name,
            event_category=event_category,
            http_path=http_path,
            http_method=http_method,
            query_string=query_string,
            client_ip=client_ip,
            user_agent=user_agent,
            session_key=session_key,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

    except Exception as e:
        logger.error(f"Error logging app event: {e}")


@shared_task
def generate_event_summaries():
    """
    Generate event summaries for analytics.

    Runs periodically (hourly/daily) to pre-aggregate data.
    """
    try:
        from floor_app.operations.analytics.models import EventSummary

        now = timezone.now()

        # Hourly summary
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        EventSummary.generate_summary('HOUR', hour_start, hour_end)

        # Daily summary (if start of day)
        if now.hour == 0:
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            EventSummary.generate_summary('DAY', day_start, day_end)

        logger.info("Event summaries generated successfully")

    except Exception as e:
        logger.error(f"Error generating event summaries: {e}")


@shared_task
def generate_request_trends():
    """
    Generate information request trends.

    Runs daily to aggregate request statistics.
    """
    try:
        from floor_app.operations.analytics.models import RequestTrend

        now = timezone.now()

        # Daily trend
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        RequestTrend.generate_trend('DAY', day_start, day_end)

        logger.info("Request trends generated successfully")

    except Exception as e:
        logger.error(f"Error generating request trends: {e}")


@shared_task
def run_automation_rules(rule_scope=None):
    """
    Execute all active automation rules.

    Args:
        rule_scope: Optional filter by scope (e.g., 'INVENTORY', 'PRODUCTION')

    Runs periodically based on rule schedules.
    """
    try:
        from floor_app.operations.analytics.rule_engine.evaluator import RuleEvaluator

        results = RuleEvaluator.evaluate_all_active_rules(rule_scope=rule_scope)

        logger.info(
            f"Automation rules executed: {results['total_evaluated']} evaluated, "
            f"{results['total_triggered']} triggered, {results['total_errors']} errors"
        )

        return results

    except Exception as e:
        logger.error(f"Error running automation rules: {e}")
        return {'error': str(e)}


@shared_task
def run_single_rule(rule_id, target_object_id=None, target_model=None):
    """
    Execute a single automation rule.

    Args:
        rule_id: AutomationRule ID
        target_object_id: Optional specific object ID to evaluate
        target_model: Optional model path (e.g., 'production.JobCard')
    """
    try:
        from floor_app.operations.analytics.models import AutomationRule
        from django.apps import apps

        rule = AutomationRule.objects.get(id=rule_id)

        # Get target object if specified
        target_object = None
        if target_object_id and target_model:
            app_label, model_name = target_model.split('.')
            model = apps.get_model(app_label, model_name)
            target_object = model.objects.get(id=target_object_id)

        # Execute rule
        execution = rule.execute(target_object=target_object)

        return {
            'rule_code': rule.rule_code,
            'execution_id': execution.id,
            'triggered': execution.was_triggered,
            'comment': execution.comment,
        }

    except Exception as e:
        logger.error(f"Error running rule {rule_id}: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_old_events(days=90):
    """
    Clean up old events to prevent database bloat.

    Args:
        days: Keep events newer than this many days

    Runs weekly to remove old event logs.
    """
    try:
        from floor_app.operations.analytics.models import AppEvent

        cutoff_date = timezone.now() - timedelta(days=days)

        deleted_count, _ = AppEvent.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()

        logger.info(f"Cleaned up {deleted_count} old events (older than {days} days)")

        return {'deleted_count': deleted_count}

    except Exception as e:
        logger.error(f"Error cleaning up old events: {e}")
        return {'error': str(e)}
