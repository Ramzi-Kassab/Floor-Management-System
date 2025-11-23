"""
Django management command to load initial/reference data
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Load initial reference data for HR module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if data exists'
        )

    def handle(self, *args, **options):
        force = options['force']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Loading Initial Data for HR Module'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Check if data already exists
        from floor_app.operations.hr.models import Department, Position, LeaveType, Shift

        has_data = (
            Department.objects.exists() or
            Position.objects.exists() or
            LeaveType.objects.exists() or
            Shift.objects.exists()
        )

        if has_data and not force:
            self.stdout.write(self.style.WARNING(
                'Data already exists. Use --force to reload.'
            ))
            return

        # Load fixtures
        self.stdout.write('Loading fixtures...')

        try:
            call_command('loaddata', 'initial_data', app_label='hr', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Fixtures loaded successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading fixtures: {e}'))
            return

        # Report what was loaded
        self.stdout.write('')
        self.stdout.write('Data loaded:')
        self.stdout.write(f'  Departments: {Department.objects.count()}')
        self.stdout.write(f'  Positions: {Position.objects.count()}')
        self.stdout.write(f'  Leave Types: {LeaveType.objects.count()}')
        self.stdout.write(f'  Shifts: {Shift.objects.count()}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Initial data loaded successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
