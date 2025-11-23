"""
Django management command to export employee data to CSV/Excel
"""
from django.core.management.base import BaseCommand
import csv
from datetime import datetime

from floor_app.operations.hr.models import Employee


class Command(BaseCommand):
    help = 'Export employee data to CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=f'employees_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            help='Output file name'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['ACTIVE', 'TERMINATED', 'SUSPENDED', 'ON_LEAVE', 'ALL'],
            default='ACTIVE',
            help='Employee status to export'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        status = options['status']

        self.stdout.write(self.style.SUCCESS('Exporting employee data...'))

        # Build queryset
        queryset = Employee.objects.select_related(
            'person', 'department', 'position'
        )

        if status != 'ALL':
            queryset = queryset.filter(employment_status=status)

        # Export to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow([
                'Employee Code',
                'First Name',
                'Last Name',
                'Email',
                'Phone',
                'Department',
                'Position',
                'Hire Date',
                'Status',
                'Employee Type',
            ])

            # Data
            count = 0
            for emp in queryset:
                writer.writerow([
                    emp.employee_code,
                    emp.person.first_name if emp.person else '',
                    emp.person.last_name if emp.person else '',
                    emp.person.email if emp.person else '',
                    emp.person.phone if emp.person else '',
                    emp.department.name if emp.department else '',
                    emp.position.title if emp.position else '',
                    emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else '',
                    emp.get_employment_status_display(),
                    emp.get_employee_type_display() if hasattr(emp, 'get_employee_type_display') else '',
                ])
                count += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Exported {count} employees to {output_file}'))
