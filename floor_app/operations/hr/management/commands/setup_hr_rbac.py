"""
Management command to setup HR RBAC Groups and Permissions.

Creates Django auth Groups with appropriate permissions for HR roles,
and optionally links them to Position records.

Usage:
    python manage.py setup_hr_rbac
    python manage.py setup_hr_rbac --link-positions
    python manage.py setup_hr_rbac --create-sample-data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from floor_app.operations.hr.models import (
    HRPeople, HREmployee, HRPhone, HREmail, Position, Department
)
from floor_app.operations.models import Address


class Command(BaseCommand):
    help = 'Setup HR RBAC Groups and Permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--link-positions',
            action='store_true',
            help='Link groups to existing Position records based on name matching'
        )
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample departments, positions, and link groups'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Setting up HR RBAC Groups and Permissions...'))

        with transaction.atomic():
            # Create groups with permissions
            groups_config = self.get_groups_config()

            for group_name, config in groups_config.items():
                group, created = Group.objects.get_or_create(name=group_name)

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created group: {group_name}'))
                else:
                    self.stdout.write(f'Group exists: {group_name}')

                # Clear existing permissions and set new ones
                group.permissions.clear()

                # Add permissions
                for perm_codename in config.get('permissions', []):
                    try:
                        perm = Permission.objects.get(codename=perm_codename)
                        group.permissions.add(perm)
                        self.stdout.write(f'  Added permission: {perm_codename}')
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'  Permission not found: {perm_codename}')
                        )

            # Create custom permissions if they don't exist
            self.create_custom_permissions()

            # Link positions if requested
            if options['link_positions']:
                self.link_positions_to_groups(groups_config)

            # Create sample data if requested
            if options['create_sample_data']:
                self.create_sample_data(groups_config)

        self.stdout.write(self.style.SUCCESS('HR RBAC setup complete!'))

    def get_groups_config(self):
        """
        Define groups and their permissions.
        Maps group names to permission codenames.
        """
        return {
            # HR Management - Full access to HR module
            'hr_managers': {
                'description': 'HR Managers - Full HR module access',
                'permissions': [
                    # HRPeople permissions
                    'add_hrpeople', 'change_hrpeople', 'delete_hrpeople', 'view_hrpeople',
                    # HREmployee permissions
                    'add_hremployee', 'change_hremployee', 'delete_hremployee', 'view_hremployee',
                    # HRPhone permissions
                    'add_hrphone', 'change_hrphone', 'delete_hrphone', 'view_hrphone',
                    # HREmail permissions
                    'add_hremail', 'change_hremail', 'delete_hremail', 'view_hremail',
                    # Address permissions
                    'add_address', 'change_address', 'delete_address', 'view_address',
                    # Department permissions
                    'add_department', 'change_department', 'delete_department', 'view_department',
                    # Position permissions
                    'add_position', 'change_position', 'delete_position', 'view_position',
                ],
                'position_patterns': ['HR Manager', 'Human Resources Manager', 'HR Director'],
            },

            # HR Officers - Can create and edit but not delete critical data
            'hr_officers': {
                'description': 'HR Officers - Create and edit employee data',
                'permissions': [
                    'add_hrpeople', 'change_hrpeople', 'view_hrpeople',
                    'add_hremployee', 'change_hremployee', 'view_hremployee',
                    'add_hrphone', 'change_hrphone', 'view_hrphone',
                    'add_hremail', 'change_hremail', 'view_hremail',
                    'add_address', 'change_address', 'view_address',
                    'view_department',
                    'view_position',
                ],
                'position_patterns': ['HR Officer', 'HR Specialist', 'HR Coordinator'],
            },

            # Production Supervisors - View HR data and manage their team
            'production_supervisors': {
                'description': 'Production Supervisors - View HR data for team management',
                'permissions': [
                    'view_hrpeople',
                    'view_hremployee',
                    'view_hrphone',
                    'view_hremail',
                    'view_address',
                    'view_department',
                    'view_position',
                ],
                'position_patterns': ['Production Supervisor', 'Shift Supervisor', 'Team Leader'],
            },

            # Department Managers - View HR data for their department
            'department_managers': {
                'description': 'Department Managers - View and limited edit for department',
                'permissions': [
                    'view_hrpeople',
                    'view_hremployee',
                    'change_hremployee',  # Can update employee status
                    'view_hrphone',
                    'view_hremail',
                    'view_address',
                    'view_department',
                    'view_position',
                ],
                'position_patterns': ['Manager', 'Department Head', 'Section Manager'],
            },

            # Regular Employees - Can only view their own profile
            'employees': {
                'description': 'Regular Employees - View own profile only',
                'permissions': [
                    'view_hrpeople',  # Limited to self via view logic
                    'view_hremployee',  # Limited to self via view logic
                    'view_hrphone',
                    'view_hremail',
                    'view_address',
                ],
                'position_patterns': ['Employee', 'Staff', 'Worker', 'Operator'],
            },

            # Administrators - System administration access
            'administrators': {
                'description': 'System Administrators - Full system access',
                'permissions': [
                    'add_hrpeople', 'change_hrpeople', 'delete_hrpeople', 'view_hrpeople',
                    'add_hremployee', 'change_hremployee', 'delete_hremployee', 'view_hremployee',
                    'add_hrphone', 'change_hrphone', 'delete_hrphone', 'view_hrphone',
                    'add_hremail', 'change_hremail', 'delete_hremail', 'view_hremail',
                    'add_address', 'change_address', 'delete_address', 'view_address',
                    'add_department', 'change_department', 'delete_department', 'view_department',
                    'add_position', 'change_position', 'delete_position', 'view_position',
                    # User management
                    'add_user', 'change_user', 'delete_user', 'view_user',
                    'add_group', 'change_group', 'delete_group', 'view_group',
                ],
                'position_patterns': ['System Administrator', 'IT Administrator', 'Admin'],
            },
        }

    def create_custom_permissions(self):
        """Create custom HR-specific permissions."""
        hr_employee_ct = ContentType.objects.get_for_model(HREmployee)

        custom_permissions = [
            ('can_export_employees', 'Can export employee data'),
            ('can_import_employees', 'Can import employee data'),
            ('can_view_salaries', 'Can view salary information'),
            ('can_modify_salaries', 'Can modify salary information'),
            ('can_terminate_employees', 'Can terminate employees'),
            ('can_view_audit_logs', 'Can view HR audit logs'),
        ]

        for codename, name in custom_permissions:
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=hr_employee_ct,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(f'Created custom permission: {codename}')

    def link_positions_to_groups(self, groups_config):
        """Link existing Position records to Groups based on name matching."""
        self.stdout.write('\nLinking Positions to Groups...')

        for group_name, config in groups_config.items():
            group = Group.objects.get(name=group_name)
            patterns = config.get('position_patterns', [])

            for pattern in patterns:
                positions = Position.objects.filter(
                    name__icontains=pattern,
                    is_deleted=False
                )

                for position in positions:
                    if position.auth_group != group:
                        position.auth_group = group
                        position.save(update_fields=['auth_group'])
                        self.stdout.write(
                            f'  Linked Position "{position.name}" to Group "{group_name}"'
                        )

    def create_sample_data(self, groups_config):
        """Create sample departments, positions, and link groups."""
        self.stdout.write('\nCreating sample departments and positions...')

        # Sample departments
        departments_data = [
            {'name': 'Human Resources', 'type': 'SUPPORT'},
            {'name': 'Production', 'type': 'PRODUCTION'},
            {'name': 'Quality Assurance', 'type': 'PRODUCTION'},
            {'name': 'IT & Systems', 'type': 'SUPPORT'},
            {'name': 'Finance', 'type': 'SUPPORT'},
            {'name': 'Executive Management', 'type': 'MANAGEMENT'},
        ]

        departments = {}
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'department_type': dept_data['type']}
            )
            departments[dept_data['name']] = dept
            if created:
                self.stdout.write(f'  Created department: {dept_data["name"]}')

        # Sample positions with group mappings
        positions_data = [
            # HR positions
            {
                'name': 'HR Manager',
                'department': 'Human Resources',
                'level': 'MANAGER',
                'grade': 'GRADE_A',
                'group': 'hr_managers'
            },
            {
                'name': 'HR Officer',
                'department': 'Human Resources',
                'level': 'SENIOR',
                'grade': 'GRADE_C',
                'group': 'hr_officers'
            },
            {
                'name': 'HR Assistant',
                'department': 'Human Resources',
                'level': 'ENTRY',
                'grade': 'GRADE_D',
                'group': 'employees'
            },

            # Production positions
            {
                'name': 'Production Supervisor',
                'department': 'Production',
                'level': 'SUPERVISOR',
                'grade': 'GRADE_B',
                'group': 'production_supervisors'
            },
            {
                'name': 'Production Operator',
                'department': 'Production',
                'level': 'ENTRY',
                'grade': 'GRADE_E',
                'group': 'employees'
            },
            {
                'name': 'Senior Production Operator',
                'department': 'Production',
                'level': 'SENIOR',
                'grade': 'GRADE_D',
                'group': 'employees'
            },

            # QA positions
            {
                'name': 'QA Manager',
                'department': 'Quality Assurance',
                'level': 'MANAGER',
                'grade': 'GRADE_B',
                'group': 'department_managers'
            },
            {
                'name': 'QA Engineer',
                'department': 'Quality Assurance',
                'level': 'SENIOR',
                'grade': 'GRADE_C',
                'group': 'employees'
            },

            # IT positions
            {
                'name': 'IT Manager',
                'department': 'IT & Systems',
                'level': 'MANAGER',
                'grade': 'GRADE_B',
                'group': 'department_managers'
            },
            {
                'name': 'System Administrator',
                'department': 'IT & Systems',
                'level': 'SENIOR',
                'grade': 'GRADE_C',
                'group': 'administrators'
            },
            {
                'name': 'Software Developer',
                'department': 'IT & Systems',
                'level': 'SENIOR',
                'grade': 'GRADE_C',
                'group': 'employees'
            },

            # Finance positions
            {
                'name': 'Finance Manager',
                'department': 'Finance',
                'level': 'MANAGER',
                'grade': 'GRADE_A',
                'group': 'department_managers'
            },
            {
                'name': 'Accountant',
                'department': 'Finance',
                'level': 'SENIOR',
                'grade': 'GRADE_C',
                'group': 'employees'
            },
        ]

        for pos_data in positions_data:
            department = departments.get(pos_data['department'])
            if not department:
                continue

            group = Group.objects.filter(name=pos_data['group']).first()

            position, created = Position.objects.get_or_create(
                name=pos_data['name'],
                defaults={
                    'department': department,
                    'position_level': pos_data['level'],
                    'salary_grade': pos_data['grade'],
                    'auth_group': group,
                    'is_active': True,
                }
            )

            if created:
                self.stdout.write(
                    f'  Created position: {pos_data["name"]} '
                    f'(Group: {pos_data["group"]})'
                )
            elif position.auth_group != group:
                position.auth_group = group
                position.save(update_fields=['auth_group'])
                self.stdout.write(
                    f'  Updated position: {pos_data["name"]} '
                    f'(Group: {pos_data["group"]})'
                )

        self.stdout.write(self.style.SUCCESS('Sample data created!'))
