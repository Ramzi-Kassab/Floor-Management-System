"""
Django management command to generate test data for the Floor Management System
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta
import random

from floor_app.operations.hr.models import (
    Person, Department, Position, Employee, Contract,
    Shift, ShiftAssignment, Asset, AssetAssignment,
    LeaveType, LeaveRequest
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate test data for Floor Management System'

    def add_arguments(self, parser):
        parser.add_argument(
            '--size',
            type=str,
            default='standard',
            help='Size of dataset: minimal, standard, or large'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating'
        )

    def handle(self, *args, **options):
        size = options['size']
        clear = options['clear']

        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS(f'Generating {size} dataset...'))

        if size == 'minimal':
            self.generate_minimal()
        elif size == 'large':
            self.generate_large()
        else:
            self.generate_standard()

        self.stdout.write(self.style.SUCCESS('Test data generated successfully!'))

    def clear_data(self):
        """Clear existing test data"""
        Employee.objects.all().delete()
        Person.objects.all().delete()
        Department.objects.all().delete()
        Position.objects.all().delete()
        LeaveType.objects.all().delete()
        Asset.objects.all().delete()
        Shift.objects.all().delete()

    def generate_minimal(self):
        """Generate minimal dataset for quick testing"""
        self.stdout.write('Creating minimal dataset...')

        # Create departments
        departments = self.create_departments(5)

        # Create positions
        positions = self.create_positions(10)

        # Create employees
        employees = self.create_employees(20, departments, positions)

        # Create leave types
        leave_types = self.create_leave_types()

        # Create shifts
        shifts = self.create_shifts()

        # Create assets
        assets = self.create_assets(10)

    def generate_standard(self):
        """Generate standard dataset for development"""
        self.stdout.write('Creating standard dataset...')

        departments = self.create_departments(10)
        positions = self.create_positions(25)
        employees = self.create_employees(100, departments, positions)
        leave_types = self.create_leave_types()
        shifts = self.create_shifts()
        assets = self.create_assets(50)

        # Create some contracts
        self.create_contracts(employees[:50])

        # Create some shift assignments
        self.create_shift_assignments(employees[:30], shifts)

        # Create some asset assignments
        self.create_asset_assignments(employees[:20], assets)

        # Create some leave requests
        self.create_leave_requests(employees[:40], leave_types)

    def generate_large(self):
        """Generate large dataset for load testing"""
        self.stdout.write('Creating large dataset...')

        departments = self.create_departments(20)
        positions = self.create_positions(50)
        employees = self.create_employees(500, departments, positions)
        leave_types = self.create_leave_types()
        shifts = self.create_shifts()
        assets = self.create_assets(200)

        self.create_contracts(employees[:300])
        self.create_shift_assignments(employees[:200], shifts)
        self.create_asset_assignments(employees[:150], assets)
        self.create_leave_requests(employees[:250], leave_types)

    def create_departments(self, count):
        """Create department records"""
        self.stdout.write(f'Creating {count} departments...')
        departments = []
        dept_data = [
            ('HR', 'Human Resources'),
            ('IT', 'Information Technology'),
            ('OPS', 'Operations'),
            ('FIN', 'Finance'),
            ('SALES', 'Sales'),
            ('MKT', 'Marketing'),
            ('ENG', 'Engineering'),
            ('PROD', 'Production'),
            ('QA', 'Quality Assurance'),
            ('LOG', 'Logistics'),
            ('RND', 'Research & Development'),
            ('ADMIN', 'Administration'),
            ('SEC', 'Security'),
            ('MAINT', 'Maintenance'),
            ('WH', 'Warehouse'),
            ('PROC', 'Procurement'),
            ('PLAN', 'Planning'),
            ('CS', 'Customer Service'),
            ('PM', 'Project Management'),
            ('TRAIN', 'Training'),
        ]

        for i in range(min(count, len(dept_data))):
            code, name = dept_data[i]
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={'name': name}
            )
            departments.append(dept)
            if created:
                self.stdout.write(f'  Created department: {code}')

        return departments

    def create_positions(self, count):
        """Create position records"""
        self.stdout.write(f'Creating {count} positions...')
        positions = []
        position_data = [
            ('MGR', 'Manager'),
            ('SUPV', 'Supervisor'),
            ('LEAD', 'Team Lead'),
            ('DEV', 'Developer'),
            ('ANALYST', 'Analyst'),
            ('TECH', 'Technician'),
            ('OP', 'Operator'),
            ('ADMIN', 'Administrator'),
            ('ASST', 'Assistant'),
            ('COORD', 'Coordinator'),
            ('SPEC', 'Specialist'),
            ('CONS', 'Consultant'),
            ('ARCH', 'Architect'),
            ('ENG', 'Engineer'),
            ('ASSOC', 'Associate'),
            ('DIR', 'Director'),
            ('VP', 'Vice President'),
            ('EXEC', 'Executive'),
            ('CLERK', 'Clerk'),
            ('REP', 'Representative'),
        ]

        for i in range(min(count, len(position_data))):
            code, title = position_data[i]
            pos, created = Position.objects.get_or_create(
                code=code,
                defaults={'title': title}
            )
            positions.append(pos)

        return positions

    def create_employees(self, count, departments, positions):
        """Create employee records"""
        self.stdout.write(f'Creating {count} employees...')
        employees = []

        first_names = ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana',
                      'Edward', 'Fiona', 'George', 'Hannah']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones',
                     'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

        genders = ['M', 'F']

        for i in range(count):
            # Create person
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)

            person = Person.objects.create(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date(random.randint(1970, 2000),
                                 random.randint(1, 12),
                                 random.randint(1, 28)),
                gender=random.choice(genders),
                email=f'{first_name.lower()}.{last_name.lower()}{i}@example.com',
                phone=f'+1{random.randint(2000000000, 9999999999)}'
            )

            # Create employee
            employee = Employee.objects.create(
                person=person,
                employee_code=f'EMP{str(i+1).zfill(4)}',
                department=random.choice(departments),
                position=random.choice(positions),
                hire_date=date.today() - timedelta(days=random.randint(30, 1825)),
                employment_status='ACTIVE'
            )
            employees.append(employee)

            if (i + 1) % 50 == 0:
                self.stdout.write(f'  Created {i + 1} employees...')

        return employees

    def create_leave_types(self):
        """Create leave type records"""
        self.stdout.write('Creating leave types...')
        leave_types = []

        leave_data = [
            ('ANNUAL', 'Annual Leave', 20),
            ('SICK', 'Sick Leave', 10),
            ('PERSONAL', 'Personal Leave', 5),
            ('MATERNITY', 'Maternity Leave', 90),
            ('PATERNITY', 'Paternity Leave', 10),
            ('UNPAID', 'Unpaid Leave', 0),
        ]

        for code, name, days in leave_data:
            lt, created = LeaveType.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'days_per_year': days,
                    'requires_approval': True
                }
            )
            leave_types.append(lt)

        return leave_types

    def create_shifts(self):
        """Create shift records"""
        self.stdout.write('Creating shifts...')
        shifts = []

        shift_data = [
            ('DAY', 'Day Shift', '08:00', '17:00'),
            ('NIGHT', 'Night Shift', '20:00', '05:00'),
            ('SWING', 'Swing Shift', '14:00', '23:00'),
        ]

        for code, name, start, end in shift_data:
            shift, created = Shift.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'start_time': start,
                    'end_time': end
                }
            )
            shifts.append(shift)

        return shifts

    def create_assets(self, count):
        """Create asset records"""
        self.stdout.write(f'Creating {count} assets...')
        assets = []

        asset_types = ['LAPTOP', 'PHONE', 'VEHICLE', 'TOOL', 'EQUIPMENT']

        for i in range(count):
            asset = Asset.objects.create(
                asset_type=random.choice(asset_types),
                name=f'Asset {i+1}',
                tag_number=f'ASSET{str(i+1).zfill(4)}',
                serial_number=f'SN{random.randint(100000, 999999)}',
                status='AVAILABLE'
            )
            assets.append(asset)

        return assets

    def create_contracts(self, employees):
        """Create contract records for employees"""
        self.stdout.write(f'Creating contracts for {len(employees)} employees...')

        contract_types = ['FULL_TIME', 'PART_TIME', 'CONTRACT']

        for employee in employees:
            Contract.objects.create(
                employee=employee,
                contract_type=random.choice(contract_types),
                start_date=employee.hire_date,
                end_date=employee.hire_date + timedelta(days=365),
                salary=random.randint(30000, 120000)
            )

    def create_shift_assignments(self, employees, shifts):
        """Create shift assignments"""
        self.stdout.write(f'Creating shift assignments for {len(employees)} employees...')

        for employee in employees:
            ShiftAssignment.objects.create(
                employee=employee,
                shift=random.choice(shifts),
                start_date=employee.hire_date
            )

    def create_asset_assignments(self, employees, assets):
        """Create asset assignments"""
        self.stdout.write(f'Creating asset assignments for {len(employees)} employees...')

        available_assets = [a for a in assets if a.status == 'AVAILABLE']

        for i, employee in enumerate(employees):
            if i < len(available_assets):
                asset = available_assets[i]
                AssetAssignment.objects.create(
                    asset=asset,
                    employee=employee,
                    assigned_date=employee.hire_date
                )
                asset.status = 'ASSIGNED'
                asset.save()

    def create_leave_requests(self, employees, leave_types):
        """Create leave requests"""
        self.stdout.write(f'Creating leave requests for {len(employees)} employees...')

        statuses = ['PENDING', 'APPROVED', 'REJECTED']

        for employee in employees:
            # Create 1-3 leave requests per employee
            for _ in range(random.randint(1, 3)):
                start_date = date.today() + timedelta(days=random.randint(-30, 60))
                LeaveRequest.objects.create(
                    employee=employee,
                    leave_type=random.choice(leave_types),
                    start_date=start_date,
                    end_date=start_date + timedelta(days=random.randint(1, 5)),
                    reason='Test leave request',
                    status=random.choice(statuses)
                )
