"""
Management command to clean up old logs

Usage:
    python manage.py cleanup_logs
    python manage.py cleanup_logs --days 90
    python manage.py cleanup_logs --dry-run
"""
from django.core.management.base import BaseCommand
from floor_app.core.utils import cleanup_old_logs


class Command(BaseCommand):
    help = 'Clean up old audit logs and activity logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep (default: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write(self.style.HTTP_INFO('LOG CLEANUP'))
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be deleted'))
            self.stdout.write('')

            # Count what would be deleted
            from django.utils import timezone
            from datetime import timedelta
            from floor_app.core.models import ActivityLog, SystemEvent

            cutoff_date = timezone.now() - timedelta(days=days)

            activity_count = ActivityLog.objects.filter(
                timestamp__lt=cutoff_date
            ).count()

            event_count = SystemEvent.objects.filter(
                timestamp__lt=cutoff_date,
                is_resolved=True
            ).count()

            self.stdout.write(f"Cutoff Date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
            self.stdout.write(f"Records to be deleted:")
            self.stdout.write(f"  Activity Logs: {activity_count}")
            self.stdout.write(f"  Resolved System Events: {event_count}")
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Run without --dry-run to perform cleanup'))

        else:
            # Confirm before deletion
            self.stdout.write(self.style.WARNING(
                f'This will delete logs older than {days} days.'
            ))
            confirm = input('Are you sure you want to continue? [y/N]: ')

            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('Cleanup cancelled'))
                return

            # Perform cleanup
            result = cleanup_old_logs(days=days)

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Cleanup completed successfully!'))
            self.stdout.write('')
            self.stdout.write(f"Deleted:")
            self.stdout.write(f"  Activity Logs: {result['activity_logs']}")
            self.stdout.write(f"  Resolved System Events: {result['resolved_events']}")
            self.stdout.write(f"  Cutoff Date: {result['cutoff_date'].strftime('%Y-%m-%d %H:%M:%S')}")

        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
