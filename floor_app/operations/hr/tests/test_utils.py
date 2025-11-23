"""
Tests for HR utilities
"""
from django.test import TestCase
from datetime import date

from floor_app.operations.hr.models import Person, Department, Position, Employee
from floor_app.operations.hr.utils.qr_utils import (
    get_or_create_employee_qr,
    generate_employee_qr_image,
    get_or_create_asset_qr,
)


class QRCodeUtilsTest(TestCase):
    """Test QR code utility functions"""

    def setUp(self):
        """Set up test data"""
        department = Department.objects.create(code='IT', name='IT')
        position = Position.objects.create(code='DEV', title='Developer')
        person = Person.objects.create(
            first_name='QR',
            last_name='Test',
            date_of_birth=date(1990, 1, 1),
            gender='M',
            email='qr.test@example.com'
        )
        self.employee = Employee.objects.create(
            person=person,
            employee_code='QRTEST001',
            department=department,
            position=position,
            hire_date=date.today()
        )

    def test_get_or_create_employee_qr(self):
        """Test getting or creating employee QR code"""
        qr_code = get_or_create_employee_qr(self.employee)
        self.assertIsNotNone(qr_code)
        self.assertEqual(qr_code.reference_id, str(self.employee.pk))

        # Test that calling again returns the same QR code
        qr_code_again = get_or_create_employee_qr(self.employee)
        self.assertEqual(qr_code.pk, qr_code_again.pk)

    def test_generate_employee_qr_image(self):
        """Test generating employee QR code image"""
        qr_image = generate_employee_qr_image(self.employee)
        self.assertIsNotNone(qr_image)
        # QR image should be a PIL Image or similar


class EmployeeUtilsTest(TestCase):
    """Test employee utility functions"""

    def setUp(self):
        """Set up test data"""
        self.department = Department.objects.create(code='HR', name='HR')
        self.position = Position.objects.create(code='MGR', title='Manager')
        person = Person.objects.create(
            first_name='Test',
            last_name='User',
            date_of_birth=date(1985, 3, 15),
            gender='F'
        )
        self.employee = Employee.objects.create(
            person=person,
            employee_code='TEST001',
            department=self.department,
            position=self.position,
            hire_date=date.today()
        )

    def test_employee_active_status(self):
        """Test employee active status"""
        self.assertEqual(self.employee.employment_status, 'ACTIVE')

        # Test filtering active employees
        active_employees = Employee.objects.filter(employment_status='ACTIVE')
        self.assertIn(self.employee, active_employees)
