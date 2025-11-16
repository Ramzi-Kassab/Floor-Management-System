"""
End-to-End Tests for Employee Creation Flow

Tests the complete employee creation process including:
- Person creation with contact information
- Employee record creation
- Automatic User account creation
- RBAC group assignment based on Position
- Audit logging
"""

import json
from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from floor_app.operations.hr.models import (
    HRPeople, HREmployee, HRPhone, HREmail, Department, Position, HRAuditLog
)
from floor_app.operations.models import Address
from floor_app.operations.hr.signals import EmployeeUserService

User = get_user_model()


class TestEmployeeCreationE2E(TransactionTestCase):
    """
    End-to-end tests for complete employee creation flow.
    Uses TransactionTestCase to test signal behavior.
    """

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create admin user for testing
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        self.client.login(username='testadmin', password='testpass123')

        # Create test groups
        self.hr_manager_group = Group.objects.create(name='hr_managers')
        self.employee_group = Group.objects.create(name='employees')

        # Add some permissions to groups
        hr_people_ct = ContentType.objects.get_for_model(HRPeople)
        view_perm = Permission.objects.get(
            codename='view_hrpeople',
            content_type=hr_people_ct
        )
        self.hr_manager_group.permissions.add(view_perm)
        self.employee_group.permissions.add(view_perm)

        # Create test department
        self.department = Department.objects.create(
            name='Test Department',
            department_type='PRODUCTION'
        )

        # Create test positions with group linkage
        self.hr_manager_position = Position.objects.create(
            name='HR Manager',
            department=self.department,
            position_level='MANAGER',
            salary_grade='GRADE_A',
            auth_group=self.hr_manager_group,
            is_active=True
        )

        self.employee_position = Position.objects.create(
            name='Production Operator',
            department=self.department,
            position_level='ENTRY',
            salary_grade='GRADE_E',
            auth_group=self.employee_group,
            is_active=True
        )

    def test_complete_employee_creation_flow(self):
        """
        Test complete end-to-end employee creation via APIs.
        This simulates what the wizard does step by step.
        """
        # Step 1: Create Person
        person_data = {
            'first_name_en': 'Ahmed',
            'middle_name_en': 'Mohammed',
            'last_name_en': 'Al-Rashid',
            'first_name_ar': 'أحمد',
            'middle_name_ar': 'محمد',
            'last_name_ar': 'الراشد',
            'gender': 'MALE',
            'date_of_birth': '1990-05-15',
            'date_of_birth_hijri': '1410-10-20',
            'marital_status': 'MARRIED',
            'primary_nationality_iso2': 'SA',
            'national_id': '1234567890',
        }

        response = self.client.post(
            reverse('hr:person_create_ajax'),
            data=person_data,
            content_type='application/x-www-form-urlencoded'
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data.get('success'))
        person_id = response_data.get('person_id')
        self.assertIsNotNone(person_id)

        # Verify person was created
        person = HRPeople.objects.get(pk=person_id)
        self.assertEqual(person.first_name_en, 'Ahmed')
        self.assertEqual(person.national_id, '1234567890')

        # Step 2: Add Contact Information
        contacts_data = {
            'person_id': person_id,
            'phones': json.dumps([{
                'country_code': 'SA',
                'calling_code': '+966',
                'phone_number': '0501234567',
                'phone_type': 'MOBILE',
                'use_type': 'PERSONAL',
                'channel': 'CALL_WHATSAPP',
                'label': 'Primary Mobile',
                'is_primary': True,
            }]),
            'emails': json.dumps([{
                'email': 'ahmed.alrashid@company.com',
                'kind': 'BUSINESS',
                'label': 'Work Email',
                'is_primary': True,
            }]),
            'addresses': json.dumps([{
                'building_number': '1234',
                'street_name': 'King Fahd Road',
                'district': 'Al Olaya',
                'city': 'Riyadh',
                'postal_code': '12345',
                'additional_number': '6789',
                'unit_number': '10',
                'latitude': '24.713552',
                'longitude': '46.675297',
                'type': 'HOME',
                'label': 'Home Address',
                'is_primary': True,
            }]),
        }

        response = self.client.post(
            reverse('hr:save_contacts_ajax'),
            data=contacts_data,
            content_type='application/x-www-form-urlencoded'
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data.get('success'))

        # Verify contacts were created
        phones = HRPhone.objects.filter(person=person)
        self.assertEqual(phones.count(), 1)
        self.assertEqual(phones.first().label, 'Primary Mobile')

        emails = HREmail.objects.filter(person=person)
        self.assertEqual(emails.count(), 1)
        self.assertEqual(emails.first().email, 'ahmed.alrashid@company.com')

        addresses = Address.objects.filter(hr_person=person)
        self.assertEqual(addresses.count(), 1)
        addr = addresses.first()
        self.assertEqual(addr.city, 'Riyadh')
        self.assertEqual(float(addr.latitude), 24.713552)
        self.assertEqual(float(addr.longitude), 46.675297)

        # Step 3: Create Employee
        employee_data = {
            'person_id': person_id,
            'employee_no': 'EMP001',
            'status': 'ACTIVE',
            'department_id': self.department.id,
            'position_id': self.hr_manager_position.id,
            'contract_type': 'PERMANENT',
            'hire_date': '2024-01-15',
            'work_days_per_week': 5,
            'hours_per_week': 40,
            'shift_pattern': 'DAY',
            'salary_grade': 'GRADE_A',
            'monthly_salary': '25000.00',
            'benefits_eligible': True,
            'overtime_eligible': False,
            'annual_leave_days': 30,
            'sick_leave_days': 15,
            'special_leave_days': 5,
            'employment_category': 'REGULAR',
            'employment_status': 'ACTIVE',
            'cost_center': 'CC001',
        }

        response = self.client.post(
            reverse('hr:save_employee_ajax'),
            data=employee_data,
            content_type='application/x-www-form-urlencoded'
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data.get('success'))

        # Verify employee was created
        employee = HREmployee.objects.get(employee_no='EMP001')
        self.assertEqual(employee.person, person)
        self.assertEqual(employee.position, self.hr_manager_position)
        self.assertEqual(employee.department, self.department)

        # CRITICAL: Verify automatic User creation
        self.assertIsNotNone(employee.user, "User should be automatically created")
        user = employee.user

        # Verify user details
        self.assertEqual(user.first_name, 'Ahmed')
        self.assertEqual(user.last_name, 'Al-Rashid')
        self.assertEqual(user.email, 'ahmed.alrashid@company.com')
        self.assertTrue(user.username.startswith('ahmed'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

        # CRITICAL: Verify RBAC group assignment
        self.assertIn(
            self.hr_manager_group,
            user.groups.all(),
            "User should be added to hr_managers group based on Position"
        )

        # Verify audit logs
        audit_logs = HRAuditLog.objects.filter(employee=employee)
        self.assertGreater(audit_logs.count(), 0, "Audit logs should be created")

        # Check for USER_CREATED action
        user_created_log = audit_logs.filter(action='USER_CREATED').first()
        self.assertIsNotNone(user_created_log)
        self.assertEqual(user_created_log.affected_user, user)

        # Check for GROUP_ADDED action
        group_added_log = audit_logs.filter(action='GROUP_ADDED').first()
        self.assertIsNotNone(group_added_log)

        # Verify data appears in list views
        # Check person list
        response = self.client.get(reverse('hr:people_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ahmed')

        # Check employee list
        response = self.client.get(reverse('hr:employee_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EMP001')

    def test_position_change_updates_groups(self):
        """Test that changing an employee's position updates their groups."""
        # Create person and employee with initial position
        person = HRPeople.objects.create(
            first_name_en='Test',
            last_name_en='User',
            gender='MALE',
            date_of_birth='1995-01-01',
            primary_nationality_iso2='SA',
            national_id='1111111111'
        )

        HREmail.objects.create(
            person=person,
            email='test.user@company.com',
            kind='BUSINESS',
            is_primary_hint=True
        )

        employee = HREmployee.objects.create(
            person=person,
            employee_no='EMP002',
            status='ACTIVE',
            position=self.employee_position,
            department=self.department,
            hire_date='2024-01-01',
        )

        # Verify initial group assignment
        user = employee.user
        self.assertIsNotNone(user)
        self.assertIn(self.employee_group, user.groups.all())
        self.assertNotIn(self.hr_manager_group, user.groups.all())

        # Change position to HR Manager
        employee.position = self.hr_manager_position
        employee.save()

        # Refresh user from DB
        user.refresh_from_db()

        # Verify group change
        self.assertIn(
            self.hr_manager_group,
            user.groups.all(),
            "User should now be in hr_managers group"
        )
        self.assertNotIn(
            self.employee_group,
            user.groups.all(),
            "User should be removed from employees group"
        )

        # Verify audit log for position change
        position_change_log = HRAuditLog.objects.filter(
            employee=employee,
            action='POSITION_CHANGED'
        ).first()
        self.assertIsNotNone(position_change_log)

    def test_duplicate_email_handling(self):
        """Test that duplicate emails are handled correctly."""
        # Create first user with email
        User.objects.create_user(
            username='existing_user',
            email='duplicate@company.com',
            password='testpass'
        )

        # Create person with same email
        person = HRPeople.objects.create(
            first_name_en='Duplicate',
            last_name_en='Test',
            gender='FEMALE',
            date_of_birth='1992-03-20',
            primary_nationality_iso2='SA',
            national_id='2222222222'
        )

        HREmail.objects.create(
            person=person,
            email='duplicate@company.com',
            kind='BUSINESS',
            is_primary_hint=True
        )

        # Create employee - should handle duplicate email gracefully
        employee = HREmployee.objects.create(
            person=person,
            employee_no='EMP003',
            status='ACTIVE',
            position=self.employee_position,
            department=self.department,
            hire_date='2024-01-01',
        )

        # User should still be created with empty or different email
        self.assertIsNotNone(employee.user)
        # Either email is empty or user is linked to existing
        # Based on our implementation, it should link to existing
        # or create with different/empty email

    def test_terminated_employee_user_deactivation(self):
        """Test that terminating an employee deactivates their user."""
        person = HRPeople.objects.create(
            first_name_en='Terminated',
            last_name_en='Employee',
            gender='MALE',
            date_of_birth='1988-07-10',
            primary_nationality_iso2='SA',
            national_id='3333333333'
        )

        employee = HREmployee.objects.create(
            person=person,
            employee_no='EMP004',
            status='ACTIVE',
            position=self.employee_position,
            department=self.department,
            hire_date='2024-01-01',
        )

        user = employee.user
        self.assertTrue(user.is_active)

        # Terminate employee
        employee.status = 'TERMINATED'
        employee.save()

        # Refresh user
        user.refresh_from_db()
        self.assertFalse(user.is_active, "User should be deactivated on termination")

        # Check audit log
        deactivation_log = HRAuditLog.objects.filter(
            employee=employee,
            action='USER_DEACTIVATED'
        ).first()
        self.assertIsNotNone(deactivation_log)

    def test_username_generation_uniqueness(self):
        """Test that usernames are unique when multiple people have same name."""
        # Create first person
        person1 = HRPeople.objects.create(
            first_name_en='John',
            last_name_en='Doe',
            gender='MALE',
            date_of_birth='1990-01-01',
            primary_nationality_iso2='SA',
            national_id='4444444444'
        )

        emp1 = HREmployee.objects.create(
            person=person1,
            employee_no='EMP005',
            status='ACTIVE',
            position=self.employee_position,
            department=self.department,
            hire_date='2024-01-01',
        )

        # Create second person with same name
        person2 = HRPeople.objects.create(
            first_name_en='John',
            last_name_en='Doe',
            gender='MALE',
            date_of_birth='1991-02-02',
            primary_nationality_iso2='SA',
            national_id='5555555555'
        )

        emp2 = HREmployee.objects.create(
            person=person2,
            employee_no='EMP006',
            status='ACTIVE',
            position=self.employee_position,
            department=self.department,
            hire_date='2024-01-01',
        )

        # Verify both users exist with unique usernames
        self.assertIsNotNone(emp1.user)
        self.assertIsNotNone(emp2.user)
        self.assertNotEqual(emp1.user.username, emp2.user.username)
        self.assertTrue(emp1.user.username.startswith('john'))
        self.assertTrue(emp2.user.username.startswith('john'))

    def test_employee_service_methods(self):
        """Test EmployeeUserService class methods directly."""
        person = HRPeople.objects.create(
            first_name_en='Service',
            last_name_en='Test',
            gender='FEMALE',
            date_of_birth='1985-12-25',
            primary_nationality_iso2='SA',
            national_id='6666666666'
        )

        employee = HREmployee(
            person=person,
            employee_no='EMP007',
            status='ACTIVE',
            department=self.department,
            hire_date='2024-01-01',
        )
        employee.save()

        # Test username generation
        username = EmployeeUserService.generate_username(employee)
        self.assertIsNotNone(username)
        self.assertIn('service', username.lower())

        # Test password generation
        password = EmployeeUserService.generate_secure_password()
        self.assertEqual(len(password), 16)
        # Check for character variety
        self.assertTrue(any(c.islower() for c in password))
        self.assertTrue(any(c.isupper() for c in password))
        self.assertTrue(any(c.isdigit() for c in password))

    def test_no_broken_links_in_wizard_flow(self):
        """Test that all wizard URLs are accessible without errors."""
        wizard_urls = [
            'hr:employee_wizard_start',
            'hr:employee_wizard_contact',
            'hr:employee_wizard_employee',
            'hr:employee_wizard_review',
        ]

        for url_name in wizard_urls:
            try:
                url = reverse(url_name)
                response = self.client.get(url)
                # Should be 200 or redirect (302)
                self.assertIn(
                    response.status_code,
                    [200, 302],
                    f"URL {url_name} returned {response.status_code}"
                )
            except Exception as e:
                self.fail(f"Failed to access {url_name}: {e}")

    def test_department_and_employee_api_endpoints(self):
        """Test that the new API endpoints work correctly."""
        # Test department list API
        response = self.client.get(reverse('hr:department_list_api'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertGreater(len(data['results']), 0)

        # Test employee list API
        response = self.client.get(reverse('hr:employee_list_api'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)

        # Test with status filter
        response = self.client.get(
            reverse('hr:employee_list_api') + '?status=ACTIVE'
        )
        self.assertEqual(response.status_code, 200)


class TestRBACPermissions(TestCase):
    """Test RBAC permission enforcement."""

    def setUp(self):
        """Set up test users with different roles."""
        # Create HR Manager
        self.hr_manager_group = Group.objects.create(name='hr_managers')
        self.hr_manager = User.objects.create_user(
            username='hr_manager',
            password='testpass'
        )
        self.hr_manager.groups.add(self.hr_manager_group)

        # Create regular employee
        self.employee_group = Group.objects.create(name='employees')
        self.regular_employee = User.objects.create_user(
            username='regular_emp',
            password='testpass'
        )
        self.regular_employee.groups.add(self.employee_group)

        # Add permissions
        hr_people_ct = ContentType.objects.get_for_model(HRPeople)
        add_perm = Permission.objects.get(
            codename='add_hrpeople',
            content_type=hr_people_ct
        )
        self.hr_manager_group.permissions.add(add_perm)

    def test_hr_manager_has_add_permission(self):
        """Test that HR managers have add permission."""
        self.assertTrue(
            self.hr_manager.has_perm('hr.add_hrpeople'),
            "HR Manager should have add_hrpeople permission"
        )

    def test_regular_employee_no_add_permission(self):
        """Test that regular employees don't have add permission."""
        self.assertFalse(
            self.regular_employee.has_perm('hr.add_hrpeople'),
            "Regular employee should not have add_hrpeople permission"
        )


class TestAuditLogging(TestCase):
    """Test audit logging functionality."""

    def test_audit_log_creation(self):
        """Test that audit logs are created correctly."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        log = HRAuditLog.objects.create(
            action='USER_CREATED',
            affected_user=user,
            details=json.dumps({'test': 'data'}),
        )

        self.assertIsNotNone(log.timestamp)
        self.assertEqual(log.action, 'USER_CREATED')
        self.assertEqual(log.affected_user, user)

    def test_audit_log_string_representation(self):
        """Test audit log __str__ method."""
        user = User.objects.create_user(
            username='testuser2',
            password='testpass'
        )

        log = HRAuditLog.objects.create(
            action='GROUP_ADDED',
            affected_user=user,
            details='Test details',
        )

        str_repr = str(log)
        self.assertIn('User Added to Group', str_repr)
        self.assertIn('testuser2', str_repr)
