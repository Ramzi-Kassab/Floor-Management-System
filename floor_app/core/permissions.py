"""
Custom permissions and row-level security for Floor Management System

Provides:
- Custom permission classes for DRF
- Row-level permissions
- Department-based access control
- Manager-based hierarchical permissions
"""
from rest_framework import permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.owner == request.user


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    Permission for users to only edit their own employee record
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is editing their own employee record
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsManagerOrReadOnly(permissions.BasePermission):
    """
    Permission for managers to edit their subordinates' records
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is the employee's manager
        if hasattr(obj, 'report_to'):
            # Get current user's employee record
            try:
                from floor_app.operations.hr.models import Employee
                user_employee = Employee.objects.get(person__user=request.user)
                return obj.report_to == user_employee
            except Employee.DoesNotExist:
                return False

        return False


class IsDepartmentManagerOrReadOnly(permissions.BasePermission):
    """
    Permission for department managers to manage their department's employees
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is the department manager
        try:
            from floor_app.operations.hr.models import Employee
            user_employee = Employee.objects.get(person__user=request.user)

            # Check if user is manager of the department
            if hasattr(obj, 'department'):
                return (
                    obj.department == user_employee.department and
                    user_employee.position and
                    'manager' in user_employee.position.title.lower()
                )
        except Employee.DoesNotExist:
            return False

        return False


class CanApproveLeaveRequests(permissions.BasePermission):
    """
    Permission to check if user can approve leave requests
    """

    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user.is_authenticated:
            return False

        # Check if user has the approve_leaverequest permission
        return request.user.has_perm('hr.approve_leaverequest')

    def has_object_permission(self, request, view, obj):
        # Check if user can approve this specific leave request
        if not request.user.has_perm('hr.approve_leaverequest'):
            return False

        # User should be the employee's manager
        try:
            from floor_app.operations.hr.models import Employee
            user_employee = Employee.objects.get(person__user=request.user)

            # Check if this is a direct report or department member
            is_manager = obj.employee.report_to == user_employee
            is_dept_manager = (
                obj.employee.department == user_employee.department and
                user_employee.position and
                'manager' in user_employee.position.title.lower()
            )

            return is_manager or is_dept_manager
        except Employee.DoesNotExist:
            return False


class CanManageAssets(permissions.BasePermission):
    """
    Permission to check if user can manage company assets
    """

    def has_permission(self, request, view):
        # Read permissions allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Write permissions require specific permission
        return request.user.has_perm('hr.manage_assets')


class CanAccessHRData(permissions.BasePermission):
    """
    Permission to check if user can access HR data
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Check if user is in HR department or has HR permissions
        try:
            from floor_app.operations.hr.models import Employee
            user_employee = Employee.objects.get(person__user=request.user)

            # User is in HR department
            if user_employee.department and user_employee.department.code == 'HR':
                return True

            # Or user has specific HR permission
            return request.user.has_perm('hr.view_employee')
        except Employee.DoesNotExist:
            # Non-employee users must have explicit permission
            return request.user.has_perm('hr.view_employee')


class CanAccessPayrollData(permissions.BasePermission):
    """
    Permission to check if user can access payroll data
    Restricted to HR and Finance departments
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            from floor_app.operations.hr.models import Employee
            user_employee = Employee.objects.get(person__user=request.user)

            # User is in HR or Finance department
            if user_employee.department and user_employee.department.code in ['HR', 'FIN']:
                return True

            # Or user has specific payroll permission
            return request.user.has_perm('hr.view_payroll')
        except Employee.DoesNotExist:
            return request.user.has_perm('hr.view_payroll')


class IsInSameDepartment(permissions.BasePermission):
    """
    Permission to check if user is in the same department as the object
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        try:
            from floor_app.operations.hr.models import Employee
            user_employee = Employee.objects.get(person__user=request.user)

            # Check if object has department attribute
            if hasattr(obj, 'department'):
                return obj.department == user_employee.department
            elif hasattr(obj, 'employee'):
                # For related objects like LeaveRequest
                return obj.employee.department == user_employee.department

            return False
        except Employee.DoesNotExist:
            return False


class CanEditContract(permissions.BasePermission):
    """
    Permission to check if user can edit employment contracts
    Restricted to HR department and senior management
    """

    def has_permission(self, request, view):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Write permissions require HR access or specific permission
        return (
            request.user.has_perm('hr.change_contract') or
            request.user.has_perm('hr.add_contract')
        )

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only HR can edit contracts
        try:
            from floor_app.operations.hr.models import Employee
            user_employee = Employee.objects.get(person__user=request.user)
            return (
                user_employee.department and
                user_employee.department.code == 'HR'
            )
        except Employee.DoesNotExist:
            return request.user.has_perm('hr.change_contract')


class CanManageShifts(permissions.BasePermission):
    """
    Permission to check if user can manage shift assignments
    """

    def has_permission(self, request, view):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Write permissions require manager role or specific permission
        return request.user.has_perm('hr.manage_shifts')

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is a manager
        try:
            from floor_app.operations.hr.models import Employee
            user_employee = Employee.objects.get(person__user=request.user)
            return (
                user_employee.position and
                'manager' in user_employee.position.title.lower()
            )
        except Employee.DoesNotExist:
            return request.user.has_perm('hr.manage_shifts')


# ============================================================================
# PERMISSION HELPERS
# ============================================================================

def has_department_access(user, department):
    """
    Check if user has access to a specific department

    Args:
        user: Django User object
        department: Department object

    Returns:
        bool: True if user has access to the department
    """
    if not user.is_authenticated:
        return False

    # Superusers have access to everything
    if user.is_superuser:
        return True

    try:
        from floor_app.operations.hr.models import Employee
        user_employee = Employee.objects.get(person__user=user)

        # User is in the department
        if user_employee.department == department:
            return True

        # User is in HR department (access to all departments)
        if user_employee.department and user_employee.department.code == 'HR':
            return True

        return False
    except Employee.DoesNotExist:
        # Non-employee users need explicit permission
        return user.has_perm('hr.view_department')


def can_edit_employee(user, employee):
    """
    Check if user can edit a specific employee record

    Args:
        user: Django User object
        employee: Employee object

    Returns:
        bool: True if user can edit the employee
    """
    if not user.is_authenticated:
        return False

    # Superusers can edit anyone
    if user.is_superuser:
        return True

    try:
        from floor_app.operations.hr.models import Employee
        user_employee = Employee.objects.get(person__user=user)

        # User can edit their own record (limited fields)
        if user_employee == employee:
            return True

        # User is the employee's direct manager
        if employee.report_to == user_employee:
            return True

        # User is in HR department
        if user_employee.department and user_employee.department.code == 'HR':
            return True

        # User is a manager in the same department
        if (
            employee.department == user_employee.department and
            user_employee.position and
            'manager' in user_employee.position.title.lower()
        ):
            return True

        return False
    except Employee.DoesNotExist:
        return user.has_perm('hr.change_employee')


def can_approve_leave(user, leave_request):
    """
    Check if user can approve a specific leave request

    Args:
        user: Django User object
        leave_request: LeaveRequest object

    Returns:
        bool: True if user can approve the leave request
    """
    if not user.is_authenticated:
        return False

    # Superusers can approve anything
    if user.is_superuser:
        return True

    # Check permission
    if not user.has_perm('hr.approve_leaverequest'):
        return False

    try:
        from floor_app.operations.hr.models import Employee
        user_employee = Employee.objects.get(person__user=user)

        # User is the employee's direct manager
        if leave_request.employee.report_to == user_employee:
            return True

        # User is HR
        if user_employee.department and user_employee.department.code == 'HR':
            return True

        # User is department manager
        if (
            leave_request.employee.department == user_employee.department and
            user_employee.position and
            'manager' in user_employee.position.title.lower()
        ):
            return True

        return False
    except Employee.DoesNotExist:
        return False


def get_accessible_employees(user):
    """
    Get queryset of employees accessible to the user

    Args:
        user: Django User object

    Returns:
        QuerySet: Employee objects the user can access
    """
    from floor_app.operations.hr.models import Employee

    if not user.is_authenticated:
        return Employee.objects.none()

    # Superusers see everyone
    if user.is_superuser:
        return Employee.objects.all()

    try:
        user_employee = Employee.objects.get(person__user=user)

        # HR sees everyone
        if user_employee.department and user_employee.department.code == 'HR':
            return Employee.objects.all()

        # Managers see their direct reports and department
        if user_employee.position and 'manager' in user_employee.position.title.lower():
            from django.db.models import Q
            return Employee.objects.filter(
                Q(report_to=user_employee) |
                Q(department=user_employee.department)
            ).distinct()

        # Regular employees see themselves and their department
        return Employee.objects.filter(
            Q(pk=user_employee.pk) |
            Q(department=user_employee.department)
        ).distinct()

    except Employee.DoesNotExist:
        # Non-employees with permission can view all
        if user.has_perm('hr.view_employee'):
            return Employee.objects.all()
        return Employee.objects.none()


def create_custom_permissions():
    """
    Create custom permissions for the application

    Call this in a migration or management command
    """
    from django.contrib.contenttypes.models import ContentType
    from floor_app.operations.hr.models import Employee, LeaveRequest, Asset

    # Custom permissions for Employee
    employee_ct = ContentType.objects.get_for_model(Employee)
    Permission.objects.get_or_create(
        codename='approve_leaverequest',
        name='Can approve leave requests',
        content_type=employee_ct,
    )
    Permission.objects.get_or_create(
        codename='view_payroll',
        name='Can view payroll information',
        content_type=employee_ct,
    )
    Permission.objects.get_or_create(
        codename='terminate_employee',
        name='Can terminate employees',
        content_type=employee_ct,
    )

    # Custom permissions for Asset
    asset_ct = ContentType.objects.get_for_model(Asset)
    Permission.objects.get_or_create(
        codename='manage_assets',
        name='Can manage company assets',
        content_type=asset_ct,
    )

    # Custom permissions for Shift
    from floor_app.operations.hr.models import Shift
    shift_ct = ContentType.objects.get_for_model(Shift)
    Permission.objects.get_or_create(
        codename='manage_shifts',
        name='Can manage shift assignments',
        content_type=shift_ct,
    )
