"""
Celery configuration for Floor Management System

Provides:
- Celery app initialization
- Task scheduling
- Background job processing
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'floor_mgmt.settings')

# Create Celery app
app = Celery('floor_mgmt')

# Load configuration from Django settings with 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Celery Beat Schedule for Periodic Tasks
app.conf.beat_schedule = {
    # Cleanup old audit logs every week
    'cleanup-old-logs': {
        'task': 'floor_app.core.tasks.cleanup_old_audit_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Every Sunday at 2 AM
    },

    # Send daily activity summary
    'daily-activity-summary': {
        'task': 'floor_app.core.tasks.send_daily_activity_summary',
        'schedule': crontab(hour=18, minute=0),  # Every day at 6 PM
    },

    # Check expiring contracts
    'check-expiring-contracts': {
        'task': 'floor_app.operations.hr.tasks.check_expiring_contracts',
        'schedule': crontab(hour=9, minute=0),  # Every day at 9 AM
    },

    # Process pending leave requests
    'process-pending-leave-requests': {
        'task': 'floor_app.operations.hr.tasks.send_pending_leave_reminders',
        'schedule': crontab(hour=10, minute=0, day_of_week='1,4'),  # Monday and Thursday at 10 AM
    },

    # Generate weekly reports
    'generate-weekly-reports': {
        'task': 'floor_app.core.tasks.generate_weekly_reports',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Every Monday at 8 AM
    },

    # Check system health
    'check-system-health': {
        'task': 'floor_app.core.tasks.check_system_health',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },

    # Sync asset inventory
    'sync-asset-inventory': {
        'task': 'floor_app.operations.hr.tasks.sync_asset_inventory',
        'schedule': crontab(hour=1, minute=0),  # Every day at 1 AM
    },
}

# Celery Configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Broker settings
    broker_connection_retry_on_startup=True,
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'
