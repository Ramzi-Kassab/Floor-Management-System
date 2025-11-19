"""
Management command to load comprehensive test data.

Usage:
    python manage.py load_test_data
    python manage.py load_test_data --clear  # Clear existing data first
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta


User = get_user_model()


class Command(BaseCommand):
    help = 'Load comprehensive test data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before loading',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading test data...'))

        if options['clear']:
            self.clear_data()

        with transaction.atomic():
            users = self.create_users()
            departments = self.create_departments()
            locations = self.create_locations()
            cost_centers = self.create_cost_centers()

            self.stdout.write(self.style.SUCCESS(
                f'\nSuccessfully loaded test data:'
                f'\n  - {len(users)} users'
                f'\n  - {len(departments)} departments'
                f'\n  - {len(locations)} locations'
                f'\n  - {len(cost_centers)} cost centers'
            ))

    def clear_data(self):
        """Clear existing test data."""
        self.stdout.write('Clearing existing test data...')

        # Clear in reverse dependency order
        from floor_app.operations.hr.models import Department
        from floor_app.operations.inventory.models import Location
        from core.models import CostCenter

        # Keep superuser, delete test users
        User.objects.filter(is_superuser=False, username__startswith='test').delete()
        Department.objects.filter(code__startswith='TEST').delete()
        Location.objects.filter(code__startswith='TEST').delete()
        CostCenter.objects.filter(code__startswith='TEST').delete()

        self.stdout.write(self.style.SUCCESS('✓ Cleared existing test data'))

    def create_users(self):
        """Create test users."""
        self.stdout.write('Creating users...')

        users = []

        # Production Manager
        user, created = User.objects.get_or_create(
            username='prod_manager',
            defaults={
                'email': 'prod.manager@floormanagement.local',
                'first_name': 'John',
                'last_name': 'Production',
                'is_staff': True,
                'is_active': True,
            }
        )
        if created:
            user.set_password('test123')
            user.save()
            users.append(user)

        # QC Inspector
        user, created = User.objects.get_or_create(
            username='qc_inspector',
            defaults={
                'email': 'qc.inspector@floormanagement.local',
                'first_name': 'Jane',
                'last_name': 'Quality',
                'is_staff': True,
                'is_active': True,
            }
        )
        if created:
            user.set_password('test123')
            user.save()
            users.append(user)

        # Warehouse Clerk
        user, created = User.objects.get_or_create(
            username='warehouse_clerk',
            defaults={
                'email': 'warehouse@floormanagement.local',
                'first_name': 'Bob',
                'last_name': 'Warehouse',
                'is_staff': True,
                'is_active': True,
            }
        )
        if created:
            user.set_password('test123')
            user.save()
            users.append(user)

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))
        return users

    def create_departments(self):
        """Create test departments."""
        self.stdout.write('Creating departments...')

        from floor_app.operations.hr.models import Department

        departments = []

        dept_data = [
            ('PROD', 'Production', 'Manufacturing and production'),
            ('QC', 'Quality Control', 'Quality assurance and testing'),
            ('MAINT', 'Maintenance', 'Equipment maintenance'),
            ('WARE', 'Warehouse', 'Inventory management'),
            ('SALES', 'Sales', 'Customer relations and sales'),
        ]

        for code, name, description in dept_data:
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True,
                }
            )
            if created:
                departments.append(dept)

        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {len(departments)} departments'
        ))
        return departments

    def create_locations(self):
        """Create test locations."""
        self.stdout.write('Creating locations...')

        from floor_app.operations.inventory.models import Location

        locations = []

        location_data = [
            ('WH-A01', 'Warehouse A - Zone 1', 'Main warehouse zone 1'),
            ('WH-A02', 'Warehouse A - Zone 2', 'Main warehouse zone 2'),
            ('WH-B01', 'Warehouse B - Zone 1', 'Secondary warehouse zone 1'),
            ('PROD-01', 'Production Floor 1', 'Main production floor'),
            ('PROD-02', 'Production Floor 2', 'Secondary production floor'),
            ('QC-01', 'QC Lab 1', 'Quality control laboratory'),
        ]

        for code, name, description in location_data:
            loc, created = Location.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True,
                }
            )
            if created:
                locations.append(loc)

        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {len(locations)} locations'
        ))
        return locations

    def create_cost_centers(self):
        """Create test cost centers."""
        self.stdout.write('Creating cost centers...')

        from core.models import CostCenter

        cost_centers = []

        cc_data = [
            ('CC-1000', 'Production - Bits', 'Bit manufacturing'),
            ('CC-2000', 'Quality Control', 'QC and testing'),
            ('CC-3000', 'Maintenance', 'Maintenance operations'),
            ('CC-4000', 'Warehouse', 'Warehouse operations'),
        ]

        for code, name, description in cc_data:
            cc, created = CostCenter.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True,
                }
            )
            if created:
                cost_centers.append(cc)

        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {len(cost_centers)} cost centers'
        ))
        return cost_centers
