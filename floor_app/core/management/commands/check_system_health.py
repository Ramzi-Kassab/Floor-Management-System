"""
Management command to check system health

Usage:
    python manage.py check_system_health
    python manage.py check_system_health --detailed
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from floor_app.core.utils import get_system_health_summary
from floor_app.core.models import SystemEvent, AuditLog, ActivityLog


class Command(BaseCommand):
    help = 'Check system health and display metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed health information',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        days = options['days']

        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write(self.style.HTTP_INFO('SYSTEM HEALTH CHECK'))
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write('')

        # Get health summary
        health = get_system_health_summary()

        # Display overall health status
        status_color = {
            'HEALTHY': self.style.SUCCESS,
            'DEGRADED': self.style.WARNING,
            'WARNING': self.style.WARNING,
            'CRITICAL': self.style.ERROR,
        }
        color_func = status_color.get(health['health_status'], self.style.WARNING)

        self.stdout.write(f"Overall Status: {color_func(health['health_status'])}")
        self.stdout.write(f"Checked at: {health['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write('')

        # Display metrics
        self.stdout.write(self.style.HTTP_INFO('Last 24 Hours:'))
        self.stdout.write(f"  Critical Events: {self.style.ERROR(str(health['critical_count']))}")
        self.stdout.write(f"  Errors: {self.style.WARNING(str(health['error_count']))}")
        self.stdout.write(f"  Warnings: {str(health['warning_count'])}")
        self.stdout.write(f"  Unresolved Events: {str(health['unresolved_count'])}")
        self.stdout.write('')

        # Show common errors
        if health['common_errors']:
            self.stdout.write(self.style.HTTP_INFO('Most Common Errors:'))
            for error in health['common_errors']:
                self.stdout.write(f"  - {error['event_name']}: {error['count']} occurrences")
            self.stdout.write('')

        # Detailed information
        if detailed:
            from datetime import timedelta

            # Calculate date range
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)

            self.stdout.write(self.style.HTTP_INFO(f'Detailed Metrics (Last {days} Days):'))
            self.stdout.write('')

            # Activity statistics
            activity_count = ActivityLog.objects.filter(
                timestamp__gte=start_date
            ).count()
            unique_users = ActivityLog.objects.filter(
                timestamp__gte=start_date
            ).values('user').distinct().count()

            self.stdout.write(f"  Total Activities: {activity_count}")
            self.stdout.write(f"  Unique Active Users: {unique_users}")
            self.stdout.write('')

            # Audit log statistics
            audit_count = AuditLog.objects.filter(
                timestamp__gte=start_date
            ).count()
            self.stdout.write(f"  Audit Log Entries: {audit_count}")
            self.stdout.write('')

            # System events by level
            self.stdout.write(self.style.HTTP_INFO('System Events by Level:'))
            for level in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
                count = SystemEvent.objects.filter(
                    timestamp__gte=start_date,
                    level=level
                ).count()
                if count > 0:
                    level_color = {
                        'CRITICAL': self.style.ERROR,
                        'ERROR': self.style.ERROR,
                        'WARNING': self.style.WARNING,
                        'INFO': self.style.SUCCESS,
                        'DEBUG': self.style.HTTP_INFO,
                    }[level]
                    self.stdout.write(f"  {level}: {level_color(str(count))}")
            self.stdout.write('')

            # System events by category
            self.stdout.write(self.style.HTTP_INFO('System Events by Category:'))
            for category, _ in SystemEvent.EVENT_CATEGORIES:
                count = SystemEvent.objects.filter(
                    timestamp__gte=start_date,
                    category=category
                ).count()
                if count > 0:
                    self.stdout.write(f"  {category}: {count}")
            self.stdout.write('')

        # Recommendations
        self.stdout.write(self.style.HTTP_INFO('Recommendations:'))
        if health['critical_count'] > 0:
            self.stdout.write(self.style.ERROR(
                f"  ⚠ URGENT: {health['critical_count']} critical event(s) require immediate attention"
            ))
        if health['error_count'] > 10:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ {health['error_count']} errors detected - investigate and resolve"
            ))
        if health['unresolved_count'] > 20:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ {health['unresolved_count']} unresolved events - review and mark as resolved"
            ))
        if health['health_status'] == 'HEALTHY':
            self.stdout.write(self.style.SUCCESS('  ✓ System is operating normally'))

        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 70))

        # Exit with error code if system is not healthy
        if health['health_status'] in ['CRITICAL', 'WARNING']:
            exit(1)
