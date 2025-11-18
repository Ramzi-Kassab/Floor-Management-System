"""
Task Scheduling and Automation for Floor Management System.

Features:
- Scheduled tasks
- Recurring tasks
- Task queue management
- Task monitoring
"""

from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
import json


class ScheduledTask:
    """
    Scheduled task definition.

    Supports:
    - One-time execution
    - Recurring execution (cron-like)
    - Task dependencies
    """

    def __init__(self, name, func, schedule_type='once', schedule_data=None,
                 enabled=True, max_retries=3):
        """
        Initialize scheduled task.

        Args:
            name: Unique task name
            func: Function to execute
            schedule_type: 'once', 'interval', 'cron', 'daily', 'weekly'
            schedule_data: Dict with schedule configuration
            enabled: Whether task is enabled
            max_retries: Maximum retry attempts on failure
        """
        self.name = name
        self.func = func
        self.schedule_type = schedule_type
        self.schedule_data = schedule_data or {}
        self.enabled = enabled
        self.max_retries = max_retries

    def should_run(self):
        """Check if task should run now."""
        if not self.enabled:
            return False

        last_run = self.get_last_run()

        if self.schedule_type == 'once':
            # Run only if never run before
            return last_run is None

        elif self.schedule_type == 'interval':
            # Run at specified intervals
            if last_run is None:
                return True

            interval = self.schedule_data.get('interval', 3600)  # Default 1 hour
            return (timezone.now() - last_run).total_seconds() >= interval

        elif self.schedule_type == 'daily':
            # Run daily at specified time
            if last_run is None:
                return True

            hour = self.schedule_data.get('hour', 0)
            minute = self.schedule_data.get('minute', 0)

            now = timezone.now()
            if last_run.date() < now.date():
                # New day - check if time has passed
                if now.hour > hour or (now.hour == hour and now.minute >= minute):
                    return True

            return False

        elif self.schedule_type == 'weekly':
            # Run weekly on specified day and time
            if last_run is None:
                return True

            day_of_week = self.schedule_data.get('day_of_week', 0)  # Monday = 0
            hour = self.schedule_data.get('hour', 0)
            minute = self.schedule_data.get('minute', 0)

            now = timezone.now()
            if (now - last_run).days >= 7:
                if now.weekday() == day_of_week:
                    if now.hour > hour or (now.hour == hour and now.minute >= minute):
                        return True

            return False

        elif self.schedule_type == 'cron':
            # Simple cron-like scheduling
            # Format: {'minute': 0, 'hour': 3, 'day': '*', 'month': '*', 'weekday': '*'}
            if last_run is None:
                return True

            now = timezone.now()

            # Check if enough time has passed
            if (now - last_run).total_seconds() < 60:
                return False

            cron = self.schedule_data
            if cron.get('minute', '*') != '*' and now.minute != cron['minute']:
                return False
            if cron.get('hour', '*') != '*' and now.hour != cron['hour']:
                return False
            if cron.get('day', '*') != '*' and now.day != cron['day']:
                return False
            if cron.get('month', '*') != '*' and now.month != cron['month']:
                return False
            if cron.get('weekday', '*') != '*' and now.weekday() != cron['weekday']:
                return False

            return True

        return False

    def execute(self, *args, **kwargs):
        """
        Execute the task.

        Returns:
            dict: Execution result
        """
        if not self.enabled:
            return {'success': False, 'error': 'Task disabled'}

        retries = 0
        last_error = None

        while retries <= self.max_retries:
            try:
                result = self.func(*args, **kwargs)

                # Record successful execution
                self.record_execution(success=True, result=result)

                return {
                    'success': True,
                    'result': result,
                    'retries': retries
                }

            except Exception as e:
                last_error = str(e)
                retries += 1

                if retries > self.max_retries:
                    break

        # Record failed execution
        self.record_execution(success=False, error=last_error)

        return {
            'success': False,
            'error': last_error,
            'retries': retries
        }

    def get_last_run(self):
        """Get timestamp of last execution."""
        key = f'scheduled_task:{self.name}:last_run'
        timestamp = cache.get(key)
        return datetime.fromisoformat(timestamp) if timestamp else None

    def record_execution(self, success=True, result=None, error=None):
        """Record task execution."""
        # Update last run time
        key = f'scheduled_task:{self.name}:last_run'
        cache.set(key, timezone.now().isoformat(), timeout=None)

        # Record execution history
        history_key = f'scheduled_task:{self.name}:history'
        history = cache.get(history_key, [])

        history.append({
            'timestamp': timezone.now().isoformat(),
            'success': success,
            'result': str(result) if result else None,
            'error': error
        })

        # Keep last 100 executions
        if len(history) > 100:
            history = history[-100:]

        cache.set(history_key, history, timeout=86400 * 30)  # 30 days

    def get_execution_history(self, limit=10):
        """Get execution history."""
        history_key = f'scheduled_task:{self.name}:history'
        history = cache.get(history_key, [])
        return history[-limit:]


class TaskScheduler:
    """
    Task scheduler.

    Manages multiple scheduled tasks.
    """

    def __init__(self):
        self.tasks = {}

    def register_task(self, task):
        """Register a scheduled task."""
        self.tasks[task.name] = task

    def unregister_task(self, task_name):
        """Unregister a task."""
        if task_name in self.tasks:
            del self.tasks[task_name]

    def get_task(self, task_name):
        """Get a task by name."""
        return self.tasks.get(task_name)

    def run_pending(self):
        """Run all pending tasks."""
        results = {}

        for name, task in self.tasks.items():
            if task.should_run():
                result = task.execute()
                results[name] = result

        return results

    def run_all(self):
        """Force run all tasks."""
        results = {}

        for name, task in self.tasks.items():
            if task.enabled:
                result = task.execute()
                results[name] = result

        return results

    def get_status(self):
        """Get status of all tasks."""
        status = {}

        for name, task in self.tasks.items():
            last_run = task.get_last_run()
            next_run = self._calculate_next_run(task)

            status[name] = {
                'enabled': task.enabled,
                'schedule_type': task.schedule_type,
                'last_run': last_run.isoformat() if last_run else None,
                'next_run': next_run.isoformat() if next_run else None,
                'recent_history': task.get_execution_history(limit=5)
            }

        return status

    def _calculate_next_run(self, task):
        """Calculate next run time for a task."""
        if not task.enabled:
            return None

        last_run = task.get_last_run()
        now = timezone.now()

        if task.schedule_type == 'once':
            return None if last_run else now

        elif task.schedule_type == 'interval':
            interval = task.schedule_data.get('interval', 3600)
            if last_run:
                return last_run + timedelta(seconds=interval)
            return now

        elif task.schedule_type == 'daily':
            hour = task.schedule_data.get('hour', 0)
            minute = task.schedule_data.get('minute', 0)

            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if next_run <= now:
                next_run += timedelta(days=1)

            return next_run

        elif task.schedule_type == 'weekly':
            day_of_week = task.schedule_data.get('day_of_week', 0)
            hour = task.schedule_data.get('hour', 0)
            minute = task.schedule_data.get('minute', 0)

            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7

            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)

            return next_run

        return None


# Global task scheduler instance
scheduler = TaskScheduler()


def scheduled_task(schedule_type='interval', **schedule_kwargs):
    """
    Decorator for registering scheduled tasks.

    Usage:
        @scheduled_task(schedule_type='daily', hour=3, minute=0)
        def my_task():
            # Task code
            pass
    """

    def decorator(func):
        task = ScheduledTask(
            name=func.__name__,
            func=func,
            schedule_type=schedule_type,
            schedule_data=schedule_kwargs
        )

        scheduler.register_task(task)

        return func

    return decorator


# Example scheduled tasks
@scheduled_task(schedule_type='daily', hour=2, minute=0)
def cleanup_old_notifications():
    """Clean up old notifications (runs daily at 2 AM)."""
    from core.notification_utils import cleanup_old_notifications
    return cleanup_old_notifications(days=90)


@scheduled_task(schedule_type='daily', hour=3, minute=0)
def cleanup_old_activities():
    """Clean up old activity logs (runs daily at 3 AM)."""
    from core.notification_utils import cleanup_old_activities
    return cleanup_old_activities(days=365)


@scheduled_task(schedule_type='weekly', day_of_week=0, hour=1, minute=0)
def generate_weekly_reports():
    """Generate weekly reports (runs Monday at 1 AM)."""
    # Placeholder for weekly report generation
    return {'report': 'generated'}


@scheduled_task(schedule_type='interval', interval=300)  # Every 5 minutes
def check_system_health():
    """Check system health (runs every 5 minutes)."""
    # Placeholder for system health check
    return {'status': 'healthy'}
