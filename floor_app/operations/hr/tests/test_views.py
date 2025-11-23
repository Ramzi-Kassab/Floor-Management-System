"""
Tests for HR views
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date

from floor_app.operations.hr.models import (
    Person, Department, Position, Employee, LeaveType, LeaveRequest
)

User = get_user_model()


class EmployeeViewsTest(TestCase):
    """Test Employee views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

        # Create test data
        self.department = Department.objects.create(
            code='TEST',
            name='Test Department'
        )
        self.position = Position.objects.create(
            code='TST',
            title='Test Position'
        )
        self.person = Person.objects.create(
            first_name='Test',
            last_name='Employee',
            date_of_birth=date(1990, 1, 1),
            gender='M',
            email='test.employee@example.com'
        )
        self.employee = Employee.objects.create(
            person=self.person,
            employee_code='TEST001',
            department=self.department,
            position=self.position,
            hire_date=date.today(),
            employment_status='ACTIVE'
        )

    def test_employee_list_view_requires_login(self):
        """Test that employee list requires authentication"""
        response = self.client.get(reverse('hr:employee-list'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_employee_list_view_authenticated(self):
        """Test employee list view when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('hr:employee-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST001')

    def test_employee_detail_view(self):
        """Test employee detail view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('hr:employee-detail', kwargs={'pk': self.employee.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Employee')
        self.assertContains(response, 'TEST001')

    def test_employee_create_view_get(self):
        """Test employee create view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('hr:employee-create'))
        self.assertEqual(response.status_code, 200)

    def test_employee_update_view(self):
        """Test employee update view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('hr:employee-update', kwargs={'pk': self.employee.pk})
        )
        self.assertEqual(response.status_code, 200)


class DepartmentViewsTest(TestCase):
    """Test Department views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.department = Department.objects.create(
            code='IT',
            name='Information Technology'
        )

    def test_department_list_view(self):
        """Test department list view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('hr:department-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Information Technology')


class LeaveRequestViewsTest(TestCase):
    """Test LeaveRequest views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='employee',
            password='testpass123'
        )

        department = Department.objects.create(code='HR', name='HR')
        position = Position.objects.create(code='MGR', title='Manager')
        person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1985, 5, 15),
            gender='M'
        )
        self.employee = Employee.objects.create(
            person=person,
            employee_code='EMP001',
            department=department,
            position=position,
            hire_date=date.today(),
            user=self.user
        )
        self.leave_type = LeaveType.objects.create(
            code='ANNUAL',
            name='Annual Leave',
            days_per_year=20
        )

    def test_leave_request_list_view(self):
        """Test leave request list view"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('hr:leave-request-list'))
        self.assertEqual(response.status_code, 200)

    def test_leave_request_create_view(self):
        """Test leave request create view"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('hr:leave-request-create'))
        self.assertEqual(response.status_code, 200)


class SearchViewsTest(TestCase):
    """Test search functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        department = Department.objects.create(code='IT', name='IT')
        position = Position.objects.create(code='DEV', title='Developer')

        # Create multiple employees
        for i in range(5):
            person = Person.objects.create(
                first_name=f'Employee{i}',
                last_name=f'Test{i}',
                date_of_birth=date(1990, 1, 1),
                gender='M'
            )
            Employee.objects.create(
                person=person,
                employee_code=f'EMP00{i}',
                department=department,
                position=position,
                hire_date=date.today()
            )

    def test_employee_search(self):
        """Test employee search functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('hr:employee-list'),
            {'search': 'Employee0'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employee0')


class QRCodeViewsTest(TestCase):
    """Test QR code functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        department = Department.objects.create(code='IT', name='IT')
        position = Position.objects.create(code='DEV', title='Developer')
        person = Person.objects.create(
            first_name='QR',
            last_name='Test',
            date_of_birth=date(1990, 1, 1),
            gender='M'
        )
        self.employee = Employee.objects.create(
            person=person,
            employee_code='QRTEST',
            department=department,
            position=position,
            hire_date=date.today()
        )

    def test_employee_detail_has_qr_code(self):
        """Test that employee detail page includes QR code"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('hr:employee-detail', kwargs={'pk': self.employee.pk})
        )
        self.assertEqual(response.status_code, 200)
        # Check if QR code section is present
        self.assertContains(response, 'QR Code')
