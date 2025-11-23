"""
Management command to generate activity reports

Usage:
    python manage.py generate_activity_report
    python manage.py generate_activity_report --days 30
    python manage.py generate_activity_report --user admin
    python manage.py generate_activity_report --export excel
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from floor_app.core.models import ActivityLog, AuditLog
from floor_app.core.utils import get_user_activity_summary
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Generate activity reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Filter by username',
        )
        parser.add_argument(
            '--export',
            type=str,
            choices=['excel', 'csv', 'pdf'],
            help='Export format',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path',
        )

    def handle(self, *args, **options):
        days = options['days']
        username = options.get('user')
        export_format = options.get('export')
        output_path = options.get('output')

        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write(self.style.HTTP_INFO('ACTIVITY REPORT'))
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write('')

        # Date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        self.stdout.write(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        self.stdout.write('')

        # Build queryset
        activities = ActivityLog.objects.filter(
            timestamp__gte=start_date
        )

        if username:
            try:
                user = User.objects.get(username=username)
                activities = activities.filter(user=user)
                self.stdout.write(f"User: {username}")
                self.stdout.write('')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
                return

        # Statistics
        total_activities = activities.count()
        unique_users = activities.values('user').distinct().count()

        self.stdout.write(self.style.HTTP_INFO('Overall Statistics:'))
        self.stdout.write(f"  Total Activities: {total_activities}")
        self.stdout.write(f"  Unique Users: {unique_users}")
        self.stdout.write('')

        # Activity breakdown by type
        self.stdout.write(self.style.HTTP_INFO('Activities by Type:'))
        from django.db.models import Count
        by_type = activities.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')

        for item in by_type:
            activity_type = dict(ActivityLog.ACTIVITY_TYPES).get(
                item['activity_type'],
                item['activity_type']
            )
            self.stdout.write(f"  {activity_type}: {item['count']}")
        self.stdout.write('')

        # Most active users
        if not username:
            self.stdout.write(self.style.HTTP_INFO('Top 10 Most Active Users:'))
            top_users = activities.values('user__username').annotate(
                count=Count('id')
            ).order_by('-count')[:10]

            for idx, item in enumerate(top_users, 1):
                username_str = item['user__username'] or 'Anonymous'
                self.stdout.write(f"  {idx}. {username_str}: {item['count']} activities")
            self.stdout.write('')

        # Most visited paths
        self.stdout.write(self.style.HTTP_INFO('Top 10 Most Visited Paths:'))
        top_paths = activities.values('path').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        for idx, item in enumerate(top_paths, 1):
            self.stdout.write(f"  {idx}. {item['path']}: {item['count']} visits")
        self.stdout.write('')

        # Average duration
        from django.db.models import Avg
        activities_with_duration = activities.exclude(duration_ms__isnull=True)
        if activities_with_duration.exists():
            avg_duration = activities_with_duration.aggregate(
                avg=Avg('duration_ms')
            )['avg']
            self.stdout.write(f"Average Request Duration: {avg_duration:.2f}ms")
            self.stdout.write('')

        # Export if requested
        if export_format:
            self.export_data(
                activities,
                export_format,
                output_path,
                start_date,
                end_date
            )

        self.stdout.write(self.style.HTTP_INFO('=' * 70))

    def export_data(self, queryset, format, output_path, start_date, end_date):
        """Export data to file"""
        from floor_app.core.exports import ExcelExporter, CSVExporter, PDFExporter
        import os

        if not output_path:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"activity_report_{timestamp}.{format}"

        self.stdout.write(f"Exporting to {output_path}...")

        # Prepare data
        headers = ['Timestamp', 'User', 'Activity Type', 'Path', 'Duration (ms)', 'IP Address']
        data = [
            [
                activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                activity.user.username if activity.user else 'Anonymous',
                activity.get_activity_type_display(),
                activity.path[:100],
                activity.duration_ms or '',
                activity.ip_address or '',
            ]
            for activity in queryset
        ]

        try:
            if format == 'excel':
                exporter = ExcelExporter('Activity Report')
                exporter.add_sheet('Activities', headers, data)

                # Add summary
                summary = {
                    'Report Period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    'Total Activities': queryset.count(),
                    'Generated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
                exporter.add_summary_sheet('Summary', summary)

                exporter.save_to_file(output_path)

            elif format == 'csv':
                exporter = CSVExporter()
                exporter.add_row(headers)
                exporter.add_rows(data)
                exporter.save_to_file(output_path)

            elif format == 'pdf':
                exporter = PDFExporter('Activity Report')
                exporter.add_title('Activity Report')
                exporter.add_paragraph(
                    f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                )
                exporter.add_paragraph(f"Total Activities: {queryset.count()}")
                exporter.add_table(headers, data[:100])  # Limit to 100 for PDF
                exporter.save_to_file(output_path)

            self.stdout.write(self.style.SUCCESS(f'Report exported to: {output_path}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Export failed: {str(e)}'))
