"""
Tests for Position CRUD Functionality

Tests the Position management system including:
- Position list view with filtering and search
- Position detail view
- Position create/update views
- Position delete with employee validation
- Position API endpoint
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from floor_app.operations.hr.models import (
    Position, Department, HRPeople, HREmployee
)

User = get_user_model()


class TestPositionModel(TestCase):
    """Test the Position model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.department = Department.objects.create(
            name='Test Department',
            department_type='PRODUCTION'
        )

        self.group = Group.objects.create(name='test_group')

    def test_position_creation(self):
        """Test creating a position."""
        position = Position.objects.create(
            name='Test Position',
            code='POS-001',
            department=self.department,
            position_level='ENTRY',
            salary_grade='GRADE_C',
            is_active=True
        )

        self.assertEqual(position.name, 'Test Position')
        self.assertEqual(position.code, 'POS-001')
        self.assertEqual(position.department, self.department)
        self.assertTrue(position.is_active)
        self.assertFalse(position.is_deleted)

    def test_position_string_representation(self):
        """Test __str__ method."""
        position = Position.objects.create(
            name='Senior Developer',
            department=self.department,
            position_level='SENIOR',
            salary_grade='GRADE_A'
        )

        self.assertEqual(str(position), 'Senior Developer')

    def test_position_with_auth_group(self):
        """Test position with linked auth group."""
        position = Position.objects.create(
            name='Manager Position',
            department=self.department,
            position_level='MANAGER',
            salary_grade='GRADE_A',
            auth_group=self.group
        )

        self.assertEqual(position.auth_group, self.group)

    def test_position_required_fields(self):
        """Test that required fields are enforced."""
        with self.assertRaises(Exception):
            # Missing required fields should raise exception
            Position.objects.create(name='Invalid Position')

    def test_position_level_choices(self):
        """Test that position level is from valid choices."""
        position = Position.objects.create(
            name='Test Position',
            department=self.department,
            position_level='EXECUTIVE',
            salary_grade='GRADE_A'
        )

        self.assertIn(position.position_level, [
            'ENTRY', 'JUNIOR', 'INTERMEDIATE', 'SENIOR',
            'LEAD', 'MANAGER', 'DIRECTOR', 'EXECUTIVE'
        ])

    def test_position_salary_grade_choices(self):
        """Test that salary grade is from valid choices."""
        position = Position.objects.create(
            name='Test Position',
            department=self.department,
            position_level='ENTRY',
            salary_grade='GRADE_E'
        )

        self.assertIn(position.salary_grade, [
            'GRADE_A', 'GRADE_B', 'GRADE_C', 'GRADE_D', 'GRADE_E'
        ])


class TestPositionListView(TestCase):
    """Test the Position list view."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=False
        )
        self.client.login(username='testuser', password='testpass123')

        self.department = Department.objects.create(
            name='Engineering',
            department_type='PRODUCTION'
        )

        # Create test positions
        self.position1 = Position.objects.create(
            name='Junior Developer',
            code='POS-JD',
            department=self.department,
            position_level='JUNIOR',
            salary_grade='GRADE_D',
            is_active=True
        )

        self.position2 = Position.objects.create(
            name='Senior Developer',
            code='POS-SD',
            department=self.department,
            position_level='SENIOR',
            salary_grade='GRADE_B',
            is_active=True
        )

        self.position3 = Position.objects.create(
            name='Inactive Position',
            code='POS-IN',
            department=self.department,
            position_level='ENTRY',
            salary_grade='GRADE_E',
            is_active=False
        )

    def test_position_list_view_loads(self):
        """Test that position list view loads correctly."""
        response = self.client.get(reverse('hr:position_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hr/position_list.html')

    def test_position_list_requires_login(self):
        """Test that position list requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('hr:position_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_position_list_shows_positions(self):
        """Test that position list shows all positions."""
        response = self.client.get(reverse('hr:position_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Junior Developer')
        self.assertContains(response, 'Senior Developer')

    def test_position_list_search(self):
        """Test search functionality."""
        response = self.client.get(
            reverse('hr:position_list'),
            {'search': 'Senior'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Senior Developer')
        self.assertNotContains(response, 'Junior Developer')

    def test_position_list_filter_by_department(self):
        """Test filtering by department."""
        other_dept = Department.objects.create(
            name='Sales',
            department_type='SALES'
        )
        Position.objects.create(
            name='Sales Manager',
            department=other_dept,
            position_level='MANAGER',
            salary_grade='GRADE_A'
        )

        response = self.client.get(
            reverse('hr:position_list'),
            {'department': self.department.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Junior Developer')
        self.assertNotContains(response, 'Sales Manager')

    def test_position_list_filter_by_level(self):
        """Test filtering by position level."""
        response = self.client.get(
            reverse('hr:position_list'),
            {'level': 'SENIOR'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Senior Developer')
        self.assertNotContains(response, 'Junior Developer')

    def test_position_list_filter_by_status(self):
        """Test filtering by active status."""
        response = self.client.get(
            reverse('hr:position_list'),
            {'is_active': 'true'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Junior Developer')
        self.assertNotContains(response, 'Inactive Position')

    def test_position_list_pagination(self):
        """Test pagination of position list."""
        # Create 25 positions
        for i in range(23):  # Already have 3
            Position.objects.create(
                name=f'Position {i}',
                department=self.department,
                position_level='ENTRY',
                salary_grade='GRADE_E'
            )

        response = self.client.get(reverse('hr:position_list'))
        self.assertEqual(response.status_code, 200)
        # Default pagination is 20
        self.assertIn('page_obj', response.context)
        self.assertLessEqual(len(response.context['page_obj']), 20)

    def test_position_list_employee_count(self):
        """Test that employee count is displayed."""
        # Create employee for position1
        person = HRPeople.objects.create(
            first_name_en='Test',
            last_name_en='Employee',
            gender='MALE',
            date_of_birth='1990-01-01',
            primary_nationality_iso2='US',
            national_id='123456789'
        )

        HREmployee.objects.create(
            person=person,
            employee_no='EMP001',
            status='ACTIVE',
            department=self.department,
            position=self.position1,
            hire_date='2024-01-01'
        )

        response = self.client.get(reverse('hr:position_list'))
        self.assertEqual(response.status_code, 200)
        # Check that position1 has employee_count annotation
        positions = response.context['positions']
        pos1 = positions.get(id=self.position1.id)
        self.assertEqual(pos1.employee_count, 1)


class TestPositionDetailView(TestCase):
    """Test the Position detail view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.department = Department.objects.create(
            name='Test Department',
            department_type='PRODUCTION'
        )

        self.position = Position.objects.create(
            name='Test Position',
            code='TST-001',
            department=self.department,
            position_level='SENIOR',
            salary_grade='GRADE_B',
            job_description='Test job description',
            is_active=True
        )

    def test_position_detail_view_loads(self):
        """Test that position detail view loads."""
        response = self.client.get(
            reverse('hr:position_detail', kwargs={'pk': self.position.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hr/position_detail.html')

    def test_position_detail_requires_login(self):
        """Test that position detail requires authentication."""
        self.client.logout()
        response = self.client.get(
            reverse('hr:position_detail', kwargs={'pk': self.position.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_position_detail_shows_information(self):
        """Test that detail view shows position information."""
        response = self.client.get(
            reverse('hr:position_detail', kwargs={'pk': self.position.pk})
        )
        self.assertContains(response, 'Test Position')
        self.assertContains(response, 'TST-001')
        self.assertContains(response, 'Test job description')

    def test_position_detail_shows_employees(self):
        """Test that detail view shows associated employees."""
        person = HRPeople.objects.create(
            first_name_en='John',
            last_name_en='Doe',
            gender='MALE',
            date_of_birth='1990-01-01',
            primary_nationality_iso2='US',
            national_id='123456789'
        )

        employee = HREmployee.objects.create(
            person=person,
            employee_no='EMP001',
            status='ACTIVE',
            department=self.department,
            position=self.position,
            hire_date='2024-01-01'
        )

        response = self.client.get(
            reverse('hr:position_detail', kwargs={'pk': self.position.pk})
        )
        self.assertContains(response, 'EMP001')
        self.assertContains(response, 'John Doe')


class TestPositionCreateView(TestCase):
    """Test the Position create view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

        self.department = Department.objects.create(
            name='Test Department',
            department_type='PRODUCTION'
        )

    def test_position_create_view_loads(self):
        """Test that create view loads."""
        response = self.client.get(reverse('hr:position_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hr/position_form.html')

    def test_position_create_requires_login(self):
        """Test that create view requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('hr:position_create'))
        self.assertEqual(response.status_code, 302)

    def test_position_create_success(self):
        """Test successful position creation."""
        data = {
            'name': 'New Position',
            'code': 'NEW-001',
            'department': self.department.id,
            'position_level': 'ENTRY',
            'salary_grade': 'GRADE_C',
            'is_active': True
        }

        response = self.client.post(reverse('hr:position_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect on success

        # Verify position was created
        position = Position.objects.get(code='NEW-001')
        self.assertEqual(position.name, 'New Position')
        self.assertEqual(position.department, self.department)

    def test_position_create_validation(self):
        """Test form validation on create."""
        # Missing required field
        data = {
            'name': 'Invalid Position',
            # Missing department
            'position_level': 'ENTRY',
            'salary_grade': 'GRADE_C'
        }

        response = self.client.post(reverse('hr:position_create'), data)
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'department', 'This field is required.')


class TestPositionUpdateView(TestCase):
    """Test the Position update view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

        self.department = Department.objects.create(
            name='Test Department',
            department_type='PRODUCTION'
        )

        self.position = Position.objects.create(
            name='Original Name',
            code='ORIG-001',
            department=self.department,
            position_level='ENTRY',
            salary_grade='GRADE_D'
        )

    def test_position_update_view_loads(self):
        """Test that update view loads."""
        response = self.client.get(
            reverse('hr:position_update', kwargs={'pk': self.position.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hr/position_form.html')

    def test_position_update_success(self):
        """Test successful position update."""
        data = {
            'name': 'Updated Name',
            'code': 'ORIG-001',
            'department': self.department.id,
            'position_level': 'SENIOR',
            'salary_grade': 'GRADE_B',
            'is_active': True
        }

        response = self.client.post(
            reverse('hr:position_update', kwargs={'pk': self.position.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)

        # Verify changes
        self.position.refresh_from_db()
        self.assertEqual(self.position.name, 'Updated Name')
        self.assertEqual(self.position.position_level, 'SENIOR')


class TestPositionDeleteView(TestCase):
    """Test the Position delete view with validation."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

        self.department = Department.objects.create(
            name='Test Department',
            department_type='PRODUCTION'
        )

        self.position = Position.objects.create(
            name='Position to Delete',
            department=self.department,
            position_level='ENTRY',
            salary_grade='GRADE_E'
        )

    def test_position_delete_view_loads(self):
        """Test that delete confirmation view loads."""
        response = self.client.get(
            reverse('hr:position_delete', kwargs={'pk': self.position.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hr/position_confirm_delete.html')

    def test_position_delete_success_no_employees(self):
        """Test successful deletion when no employees assigned."""
        response = self.client.post(
            reverse('hr:position_delete', kwargs={'pk': self.position.pk})
        )
        self.assertEqual(response.status_code, 302)

        # Verify soft delete
        self.position.refresh_from_db()
        self.assertTrue(self.position.is_deleted)
        self.assertEqual(self.position.deleted_by, self.user)

    def test_position_delete_blocked_with_active_employees(self):
        """Test that deletion is blocked when active employees exist."""
        # Create employee assigned to position
        person = HRPeople.objects.create(
            first_name_en='Active',
            last_name_en='Employee',
            gender='MALE',
            date_of_birth='1990-01-01',
            primary_nationality_iso2='US',
            national_id='123456789'
        )

        HREmployee.objects.create(
            person=person,
            employee_no='EMP001',
            status='ACTIVE',
            department=self.department,
            position=self.position,
            hire_date='2024-01-01'
        )

        response = self.client.post(
            reverse('hr:position_delete', kwargs={'pk': self.position.pk})
        )

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)

        # Verify position was NOT deleted
        self.position.refresh_from_db()
        self.assertFalse(self.position.is_deleted)

    def test_position_delete_allowed_with_deleted_employees(self):
        """Test that deletion is allowed when only deleted employees exist."""
        person = HRPeople.objects.create(
            first_name_en='Deleted',
            last_name_en='Employee',
            gender='MALE',
            date_of_birth='1990-01-01',
            primary_nationality_iso2='US',
            national_id='987654321'
        )

        employee = HREmployee.objects.create(
            person=person,
            employee_no='EMP002',
            status='TERMINATED',
            department=self.department,
            position=self.position,
            hire_date='2024-01-01',
            is_deleted=True
        )

        response = self.client.post(
            reverse('hr:position_delete', kwargs={'pk': self.position.pk})
        )
        self.assertEqual(response.status_code, 302)

        # Verify position was deleted
        self.position.refresh_from_db()
        self.assertTrue(self.position.is_deleted)


class TestPositionAPIEndpoint(TestCase):
    """Test the Position API endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.department = Department.objects.create(
            name='API Test Department',
            department_type='PRODUCTION'
        )

        self.position = Position.objects.create(
            name='API Test Position',
            code='API-001',
            department=self.department,
            position_level='SENIOR',
            salary_grade='GRADE_A',
            is_active=True
        )

    def test_position_api_requires_login(self):
        """Test that API requires authentication."""
        self.client.logout()
        response = self.client.get(reverse('hr:position_list_api'))
        self.assertEqual(response.status_code, 302)

    def test_position_api_returns_json(self):
        """Test that API returns JSON."""
        response = self.client.get(reverse('hr:position_list_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_position_api_result_format(self):
        """Test API result format."""
        response = self.client.get(reverse('hr:position_list_api'))
        data = json.loads(response.content)

        self.assertIn('results', data)
        self.assertGreater(len(data['results']), 0)

        # Check result structure
        result = data['results'][0]
        self.assertIn('id', result)
        self.assertIn('name', result)
        self.assertIn('code', result)
        self.assertIn('department__name', result)
        self.assertIn('position_level', result)

    def test_position_api_filter_by_department(self):
        """Test API filtering by department."""
        response = self.client.get(
            reverse('hr:position_list_api'),
            {'department': self.department.id}
        )
        data = json.loads(response.content)

        # All results should be from the specified department
        for result in data['results']:
            self.assertEqual(result['department'], self.department.id)

    def test_position_api_filter_by_level(self):
        """Test API filtering by level."""
        response = self.client.get(
            reverse('hr:position_list_api'),
            {'level': 'SENIOR'}
        )
        data = json.loads(response.content)

        # All results should be SENIOR level
        for result in data['results']:
            self.assertEqual(result['position_level'], 'SENIOR')

    def test_position_api_search(self):
        """Test API search functionality."""
        response = self.client.get(
            reverse('hr:position_list_api'),
            {'search': 'API Test'}
        )
        data = json.loads(response.content)

        self.assertGreater(len(data['results']), 0)
        # Should find our test position
        self.assertTrue(
            any(r['code'] == 'API-001' for r in data['results'])
        )
