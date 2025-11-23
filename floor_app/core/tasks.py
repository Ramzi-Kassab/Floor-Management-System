"""
Celery tasks for core system functions

Provides:
- System maintenance tasks
- Report generation
- Log cleanup
- Health monitoring
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='floor_app.core.tasks.cleanup_old_audit_logs')
def cleanup_old_audit_logs(days=90):
    """
    Clean up old audit logs and activity logs

    Args:
        days: Number of days to keep (default: 90)

    Returns:
        dict: Summary of deleted records
    """
    from .utils import cleanup_old_logs

    try:
        result = cleanup_old_logs(days=days)
        logger.info(f"Cleaned up old logs: {result}")
        return result
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise


@shared_task(name='floor_app.core.tasks.send_daily_activity_summary')
def send_daily_activity_summary():
    """
    Send daily activity summary to administrators

    Returns:
        int: Number of emails sent
    """
    from .models import ActivityLog, AuditLog, SystemEvent
    from django.contrib.auth.models import User

    try:
        # Get today's statistics
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))

        # Count activities
        activity_count = ActivityLog.objects.filter(timestamp__gte=today_start).count()
        audit_count = AuditLog.objects.filter(timestamp__gte=today_start).count()
        error_count = SystemEvent.objects.filter(
            timestamp__gte=today_start,
            level__in=['ERROR', 'CRITICAL']
        ).count()

        # Get admin emails
        admin_emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
        admin_emails = [email for email in admin_emails if email]

        if not admin_emails:
            logger.warning("No admin emails found for daily summary")
            return 0

        # Compose email
        subject = f'Daily Activity Summary - {today.strftime("%Y-%m-%d")}'
        message = f"""
Daily Activity Summary for {today.strftime("%B %d, %Y")}

System Activity:
- User Activities: {activity_count}
- Audit Logs: {audit_count}
- System Errors: {error_count}

{"⚠️ Warning: " + str(error_count) + " errors detected today!" if error_count > 0 else "✓ System operating normally"}

Please log in to the admin panel for more details.

---
Floor Management System
        """.strip()

        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False
        )

        logger.info(f"Sent daily activity summary to {len(admin_emails)} administrators")
        return len(admin_emails)

    except Exception as e:
        logger.error(f"Error sending daily activity summary: {e}")
        raise


@shared_task(name='floor_app.core.tasks.generate_weekly_reports')
def generate_weekly_reports():
    """
    Generate and email weekly summary reports

    Returns:
        dict: Summary of generated reports
    """
    from .models import ActivityLog, AuditLog, SystemEvent
    from django.contrib.auth.models import User
    from django.db.models import Count, Avg
    from datetime import datetime, timedelta

    try:
        # Get last week's date range
        today = timezone.now().date()
        week_start = today - timedelta(days=7)
        week_start_dt = timezone.make_aware(timezone.datetime.combine(week_start, timezone.datetime.min.time()))

        # Gather statistics
        stats = {
            'total_activities': ActivityLog.objects.filter(timestamp__gte=week_start_dt).count(),
            'total_audits': AuditLog.objects.filter(timestamp__gte=week_start_dt).count(),
            'total_errors': SystemEvent.objects.filter(
                timestamp__gte=week_start_dt,
                level__in=['ERROR', 'CRITICAL']
            ).count(),
            'unique_users': ActivityLog.objects.filter(
                timestamp__gte=week_start_dt
            ).values('user').distinct().count(),
        }

        # Top activities
        top_activities = ActivityLog.objects.filter(
            timestamp__gte=week_start_dt
        ).values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        # Most active users
        most_active = ActivityLog.objects.filter(
            timestamp__gte=week_start_dt
        ).values('user__username').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Compose email
        subject = f'Weekly System Report - {week_start.strftime("%Y-%m-%d")} to {today.strftime("%Y-%m-%d")}'

        activity_summary = '\n'.join([
            f"  - {item['activity_type']}: {item['count']}"
            for item in top_activities
        ])

        user_summary = '\n'.join([
            f"  - {item['user__username']}: {item['count']} activities"
            for item in most_active[:5]
        ])

        message = f"""
Weekly System Report
Period: {week_start.strftime("%B %d, %Y")} to {today.strftime("%B %d, %Y")}

📊 Overall Statistics:
- Total User Activities: {stats['total_activities']}
- Audit Log Entries: {stats['total_audits']}
- System Errors: {stats['total_errors']}
- Unique Active Users: {stats['unique_users']}

🔥 Top Activities:
{activity_summary}

👥 Most Active Users:
{user_summary}

{"⚠️ Note: " + str(stats['total_errors']) + " errors occurred this week. Please review." if stats['total_errors'] > 0 else "✓ System performed well this week"}

---
Floor Management System
        """.strip()

        # Send to admins
        admin_emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
        admin_emails = [email for email in admin_emails if email]

        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False
            )

            logger.info(f"Sent weekly report to {len(admin_emails)} administrators")

        return {
            'emails_sent': len(admin_emails),
            'stats': stats
        }

    except Exception as e:
        logger.error(f"Error generating weekly reports: {e}")
        raise


@shared_task(name='floor_app.core.tasks.check_system_health')
def check_system_health():
    """
    Check system health and alert if issues detected

    Returns:
        dict: System health status
    """
    from .utils import get_system_health_summary
    from .models import SystemEvent

    try:
        health = get_system_health_summary()

        # If system is not healthy, log an event
        if health['health_status'] in ['CRITICAL', 'WARNING']:
            SystemEvent.log_event(
                level='WARNING' if health['health_status'] == 'WARNING' else 'CRITICAL',
                category='SYSTEM',
                event_name='System Health Check',
                message=f"System health status: {health['health_status']}. "
                       f"Errors: {health['error_count']}, Warnings: {health['warning_count']}",
                error_count=health['error_count'],
                warning_count=health['warning_count'],
                unresolved_count=health['unresolved_count']
            )

            # If critical, send email alert
            if health['health_status'] == 'CRITICAL':
                from django.contrib.auth.models import User

                admin_emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
                admin_emails = [email for email in admin_emails if email]

                if admin_emails:
                    send_mail(
                        subject='🚨 CRITICAL: System Health Alert',
                        message=f"""
CRITICAL SYSTEM HEALTH ALERT

Status: {health['health_status']}

Issues Detected:
- Critical Events: {health['critical_count']}
- Errors: {health['error_count']}
- Unresolved Events: {health['unresolved_count']}

Please log in immediately to investigate.

---
Floor Management System
                        """.strip(),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=admin_emails,
                        fail_silently=False
                    )

        logger.info(f"System health check: {health['health_status']}")
        return health

    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        raise


@shared_task(name='floor_app.core.tasks.send_notification_email')
def send_notification_email(subject, message, recipient_list, from_email=None):
    """
    Send notification email (async)

    Args:
        subject: Email subject
        message: Email body
        recipient_list: List of recipient emails
        from_email: From email (optional, uses DEFAULT_FROM_EMAIL if not provided)

    Returns:
        int: Number of emails sent
    """
    try:
        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False
        )

        logger.info(f"Sent email to {len(recipient_list)} recipients: {subject}")
        return len(recipient_list)

    except Exception as e:
        logger.error(f"Error sending notification email: {e}")
        raise


@shared_task(name='floor_app.core.tasks.process_bulk_data_export')
def process_bulk_data_export(model_name, queryset_filters, export_format, user_email):
    """
    Process bulk data export in background

    Args:
        model_name: Name of the model to export
        queryset_filters: Dict of filters to apply
        export_format: Format ('excel', 'pdf', 'csv')
        user_email: Email to send the export to

    Returns:
        str: Export file path
    """
    from django.apps import apps
    from .exports import ExcelExporter, PDFExporter, CSVExporter
    import os

    try:
        # Get model
        model = apps.get_model('hr', model_name)

        # Build queryset
        queryset = model.objects.all()
        if queryset_filters:
            queryset = queryset.filter(**queryset_filters)

        # Generate filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{model_name}_export_{timestamp}.{export_format}"
        filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Export based on format
        if export_format == 'excel':
            from .exports import export_queryset_to_excel
            # Save to file instead of returning response
            exporter = ExcelExporter(f'{model_name} Export')
            fields = [f.name for f in model._meta.fields]
            values = list(queryset.values_list(*fields))
            exporter.add_sheet(model_name, fields, values)
            exporter.save_to_file(filepath)

        elif export_format == 'pdf':
            from .exports import PDFExporter
            exporter = PDFExporter(f'{model_name} Export')
            fields = [f.name for f in model._meta.fields]
            values = [[str(v)[:50] for v in row] for row in queryset.values_list(*fields)[:100]]
            exporter.add_title(f'{model_name} Export')
            exporter.add_table(fields, values)
            exporter.save_to_file(filepath)

        else:  # CSV
            from .exports import CSVExporter
            exporter = CSVExporter()
            fields = [f.name for f in model._meta.fields]
            exporter.add_row(fields)
            exporter.add_rows(queryset.values_list(*fields))
            exporter.save_to_file(filepath)

        # Send email with download link
        send_mail(
            subject=f'Your {model_name} export is ready',
            message=f"""
Your data export is complete!

Model: {model_name}
Format: {export_format.upper()}
Records: {queryset.count()}

The file has been saved and is available for download.

---
Floor Management System
            """.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False
        )

        logger.info(f"Completed bulk export for {model_name} ({queryset.count()} records)")
        return filepath

    except Exception as e:
        logger.error(f"Error processing bulk export: {e}")
        # Send error email
        send_mail(
            subject=f'Export failed: {model_name}',
            message=f"""
Your data export has failed.

Error: {str(e)}

Please contact support if the problem persists.

---
Floor Management System
            """.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=True
        )
        raise
