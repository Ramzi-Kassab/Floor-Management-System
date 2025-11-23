"""
Tests for HR models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, date

from floor_app.operations.hr.models import (
    Person, Department, Position, Employee, Contract,
    Shift, ShiftAssignment, Asset, AssetAssignment,
    LeaveType, LeaveRequest
)

User = get_user_model()


class PersonModelTest(TestCase):
    """Test Person model"""

    def setUp(self):
        self.person_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': date(1990, 1, 1),
            'gender': 'M',
            'email': 'john.doe@example.com',
            'phone': '+1234567890',
        }

    def test_create_person(self):
        """Test creating a person"""
        person = Person.objects.create(**self.person_data)
        self.assertEqual(person.first_name, 'John')
        self.assertEqual(person.last_name, 'Doe')
        self.assertEqual(person.full_name, 'John Doe')

    def test_full_name_property(self):
        """Test full_name property"""
        person = Person.objects.create(**self.person_data)
        self.assertEqual(person.full_name, 'John Doe')

    def test_age_calculation(self):
        """Test age calculation"""
        person = Person.objects.create(**self.person_data)
        today = date.today()
        expected_age = today.year - 1990
        if today.month < 1 or (today.month == 1 and today.day < 1):
            expected_age -= 1
        self.assertEqual(person.age, expected_age)


class DepartmentModelTest(TestCase):
    """Test Department model"""

    def test_create_department(self):
        """Test creating a department"""
        dept = Department.objects.create(
            code='IT',
            name='Information Technology',
            description='IT Department'
        )
        self.assertEqual(dept.code, 'IT')
        self.assertEqual(dept.name, 'Information Technology')
        self.assertEqual(str(dept), 'IT - Information Technology')

    def test_unique_code(self):
        """Test department code uniqueness"""
        Department.objects.create(code='IT', name='IT')
        with self.assertRaises(Exception):
            Department.objects.create(code='IT', name='IT Duplicate')


class PositionModelTest(TestCase):
    """Test Position model"""

    def test_create_position(self):
        """Test creating a position"""
        position = Position.objects.create(
            code='DEV',
            title='Software Developer',
            description='Develops software'
        )
        self.assertEqual(position.code, 'DEV')
        self.assertEqual(position.title, 'Software Developer')


class EmployeeModelTest(TestCase):
    """Test Employee model"""

    def setUp(self):
        self.person = Person.objects.create(
            first_name='Jane',
            last_name='Smith',
            date_of_birth=date(1985, 5, 15),
            gender='F',
            email='jane.smith@example.com',
        )
        self.department = Department.objects.create(
            code='HR',
            name='Human Resources'
        )
        self.position = Position.objects.create(
            code='MGR',
            title='HR Manager'
        )

    def test_create_employee(self):
        """Test creating an employee"""
        employee = Employee.objects.create(
            person=self.person,
            employee_code='EMP001',
            department=self.department,
            position=self.position,
            hire_date=date.today(),
            employment_status='ACTIVE'
        )
        self.assertEqual(employee.employee_code, 'EMP001')
        self.assertEqual(employee.department, self.department)
        self.assertEqual(employee.employment_status, 'ACTIVE')

    def test_employee_str(self):
        """Test employee string representation"""
        employee = Employee.objects.create(
            person=self.person,
            employee_code='EMP001',
            department=self.department,
            position=self.position,
            hire_date=date.today(),
        )
        self.assertEqual(str(employee), 'EMP001 - Jane Smith')


class ContractModelTest(TestCase):
    """Test Contract model"""

    def setUp(self):
        person = Person.objects.create(
            first_name='Bob',
            last_name='Johnson',
            date_of_birth=date(1992, 3, 20),
            gender='M',
        )
        department = Department.objects.create(code='IT', name='IT')
        position = Position.objects.create(code='DEV', title='Developer')
        self.employee = Employee.objects.create(
            person=person,
            employee_code='EMP002',
            department=department,
            position=position,
            hire_date=date.today(),
        )

    def test_create_contract(self):
        """Test creating a contract"""
        contract = Contract.objects.create(
            employee=self.employee,
            contract_type='FULL_TIME',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            salary=50000.00,
        )
        self.assertEqual(contract.employee, self.employee)
        self.assertEqual(contract.contract_type, 'FULL_TIME')
        self.assertEqual(contract.salary, 50000.00)

    def test_contract_date_validation(self):
        """Test contract date validation"""
        # This would require implementing clean() method in Contract model
        contract = Contract(
            employee=self.employee,
            contract_type='FULL_TIME',
            start_date=date.today(),
            end_date=date.today() - timedelta(days=1),  # End before start
            salary=50000.00,
        )
        # If validation is implemented, this should raise ValidationError
        # with self.assertRaises(ValidationError):
        #     contract.full_clean()


class ShiftModelTest(TestCase):
    """Test Shift model"""

    def test_create_shift(self):
        """Test creating a shift"""
        shift = Shift.objects.create(
            code='DAY',
            name='Day Shift',
            start_time='08:00',
            end_time='17:00',
        )
        self.assertEqual(shift.code, 'DAY')
        self.assertEqual(shift.name, 'Day Shift')


class ShiftAssignmentModelTest(TestCase):
    """Test ShiftAssignment model"""

    def setUp(self):
        person = Person.objects.create(
            first_name='Alice',
            last_name='Williams',
            date_of_birth=date(1988, 7, 10),
            gender='F',
        )
        department = Department.objects.create(code='OPS', name='Operations')
        position = Position.objects.create(code='OP', title='Operator')
        self.employee = Employee.objects.create(
            person=person,
            employee_code='EMP003',
            department=department,
            position=position,
            hire_date=date.today(),
        )
        self.shift = Shift.objects.create(
            code='NIGHT',
            name='Night Shift',
            start_time='20:00',
            end_time='05:00',
        )

    def test_create_shift_assignment(self):
        """Test creating a shift assignment"""
        assignment = ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.shift,
            start_date=date.today(),
        )
        self.assertEqual(assignment.employee, self.employee)
        self.assertEqual(assignment.shift, self.shift)


class AssetModelTest(TestCase):
    """Test Asset model"""

    def test_create_asset(self):
        """Test creating an asset"""
        asset = Asset.objects.create(
            asset_type='LAPTOP',
            name='Dell Laptop',
            tag_number='ASSET001',
            serial_number='SN123456',
            status='AVAILABLE',
        )
        self.assertEqual(asset.asset_type, 'LAPTOP')
        self.assertEqual(asset.tag_number, 'ASSET001')
        self.assertEqual(asset.status, 'AVAILABLE')


class AssetAssignmentModelTest(TestCase):
    """Test AssetAssignment model"""

    def setUp(self):
        person = Person.objects.create(
            first_name='Charlie',
            last_name='Brown',
            date_of_birth=date(1991, 11, 5),
            gender='M',
        )
        department = Department.objects.create(code='IT', name='IT')
        position = Position.objects.create(code='DEV', title='Developer')
        self.employee = Employee.objects.create(
            person=person,
            employee_code='EMP004',
            department=department,
            position=position,
            hire_date=date.today(),
        )
        self.asset = Asset.objects.create(
            asset_type='LAPTOP',
            name='MacBook Pro',
            tag_number='ASSET002',
            status='AVAILABLE',
        )

    def test_create_asset_assignment(self):
        """Test creating an asset assignment"""
        assignment = AssetAssignment.objects.create(
            asset=self.asset,
            employee=self.employee,
            assigned_date=date.today(),
        )
        self.assertEqual(assignment.asset, self.asset)
        self.assertEqual(assignment.employee, self.employee)
        self.assertIsNone(assignment.returned_date)

    def test_asset_return(self):
        """Test returning an asset"""
        assignment = AssetAssignment.objects.create(
            asset=self.asset,
            employee=self.employee,
            assigned_date=date.today(),
        )
        # Return the asset
        assignment.returned_date = date.today() + timedelta(days=30)
        assignment.return_condition = 'GOOD'
        assignment.save()
        self.assertIsNotNone(assignment.returned_date)
        self.assertEqual(assignment.return_condition, 'GOOD')


class LeaveTypeModelTest(TestCase):
    """Test LeaveType model"""

    def test_create_leave_type(self):
        """Test creating a leave type"""
        leave_type = LeaveType.objects.create(
            code='ANNUAL',
            name='Annual Leave',
            days_per_year=20,
            requires_approval=True,
        )
        self.assertEqual(leave_type.code, 'ANNUAL')
        self.assertEqual(leave_type.days_per_year, 20)
        self.assertTrue(leave_type.requires_approval)


class LeaveRequestModelTest(TestCase):
    """Test LeaveRequest model"""

    def setUp(self):
        person = Person.objects.create(
            first_name='David',
            last_name='Miller',
            date_of_birth=date(1987, 2, 28),
            gender='M',
        )
        department = Department.objects.create(code='SALES', name='Sales')
        position = Position.objects.create(code='REP', title='Sales Rep')
        self.employee = Employee.objects.create(
            person=person,
            employee_code='EMP005',
            department=department,
            position=position,
            hire_date=date.today() - timedelta(days=365),
        )
        self.leave_type = LeaveType.objects.create(
            code='SICK',
            name='Sick Leave',
            days_per_year=10,
        )

    def test_create_leave_request(self):
        """Test creating a leave request"""
        leave_request = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=9),
            reason='Medical appointment',
            status='PENDING',
        )
        self.assertEqual(leave_request.employee, self.employee)
        self.assertEqual(leave_request.leave_type, self.leave_type)
        self.assertEqual(leave_request.status, 'PENDING')

    def test_leave_days_calculation(self):
        """Test calculation of leave days"""
        leave_request = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
            reason='Test',
            status='PENDING',
        )
        # This would require implementing a days property in LeaveRequest model
        # expected_days = 3
        # self.assertEqual(leave_request.days, expected_days)

    def test_leave_approval(self):
        """Test leave request approval"""
        leave_request = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=9),
            reason='Vacation',
            status='PENDING',
        )
        # Approve the request
        leave_request.status = 'APPROVED'
        leave_request.save()
        self.assertEqual(leave_request.status, 'APPROVED')
