"""
Management command to calculate retrieval metrics for all employees.

Usage:
    python manage.py calculate_retrieval_metrics --period monthly
    python manage.py calculate_retrieval_metrics --period daily --employee-id 123
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from floor_app.operations.retrieval.services import RetrievalService

User = get_user_model()


class Command(BaseCommand):
    help = 'Calculate retrieval metrics for employees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            default='monthly',
            choices=['daily', 'weekly', 'monthly', 'quarterly', 'yearly'],
            help='Period type for metrics calculation'
        )

        parser.add_argument(
            '--employee-id',
            type=int,
            help='Calculate metrics for specific employee (optional)'
        )

        parser.add_argument(
            '--all-periods',
            action='store_true',
            help='Calculate metrics for all period types'
        )

    def handle(self, *args, **options):
        period = options['period']
        employee_id = options.get('employee_id')
        all_periods = options.get('all_periods', False)

        # Map period to period type
        period_map = {
            'daily': 'DAILY',
            'weekly': 'WEEKLY',
            'monthly': 'MONTHLY',
            'quarterly': 'QUARTERLY',
            'yearly': 'YEARLY'
        }

        # Get employees to process
        if employee_id:
            try:
                employees = [User.objects.get(pk=employee_id)]
                self.stdout.write(f"Processing single employee: {employees[0].username}")
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Employee with ID {employee_id} not found'))
                return
        else:
            employees = User.objects.filter(is_active=True)
            self.stdout.write(f"Processing {employees.count()} active employees")

        # Process metrics
        total_processed = 0
        total_created = 0

        if all_periods:
            periods_to_process = period_map.values()
        else:
            periods_to_process = [period_map[period]]

        for employee in employees:
            for period_type in periods_to_process:
                try:
                    metric = RetrievalService.calculate_and_save_metrics(employee, period_type)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ {employee.username} - {period_type}: "
                            f"{metric.accuracy_rate}% accuracy "
                            f"({metric.retrieval_requests}/{metric.total_actions})"
                        )
                    )

                    total_processed += 1
                    total_created += 1

                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(
                            f"✗ Error processing {employee.username} - {period_type}: {str(e)}"
                        )
                    )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*60}\n"
                f"Metrics calculation complete!\n"
                f"Processed: {total_processed}\n"
                f"Created/Updated: {total_created}\n"
                f"{'='*60}"
            )
        )
