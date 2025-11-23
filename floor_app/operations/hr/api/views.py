"""
REST API Views for HR Module
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from floor_app.operations.hr.models import (
    Person, Department, Position, Employee, Contract,
    Shift, ShiftAssignment, Asset, AssetAssignment,
    LeaveType, LeaveRequest
)
from .serializers import (
    PersonSerializer, DepartmentSerializer, PositionSerializer,
    EmployeeListSerializer, EmployeeDetailSerializer,
    ContractSerializer, ShiftSerializer, ShiftAssignmentSerializer,
    AssetSerializer, AssetAssignmentSerializer,
    LeaveTypeSerializer, LeaveRequestListSerializer,
    LeaveRequestDetailSerializer, LeaveRequestCreateSerializer
)


class PersonViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Person management

    list: Get all persons
    retrieve: Get specific person
    create: Create new person
    update: Update person
    partial_update: Partially update person
    destroy: Delete person
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']


class DepartmentViewSet(viewsets.ModelViewSet):
    """API endpoint for Department management"""
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'created_at']
    ordering = ['code']

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get all employees in department"""
        department = self.get_object()
        employees = department.employee_set.filter(employment_status='ACTIVE')
        serializer = EmployeeListSerializer(employees, many=True)
        return Response(serializer.data)


class PositionViewSet(viewsets.ModelViewSet):
    """API endpoint for Position management"""
    queryset = Position.objects.filter(is_active=True)
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'title', 'description']
    ordering_fields = ['code', 'title', 'created_at']
    ordering = ['code']

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get all employees in position"""
        position = self.get_object()
        employees = position.employee_set.filter(employment_status='ACTIVE')
        serializer = EmployeeListSerializer(employees, many=True)
        return Response(serializer.data)


class EmployeeViewSet(viewsets.ModelViewSet):
    """API endpoint for Employee management"""
    queryset = Employee.objects.select_related(
        'person', 'department', 'position', 'report_to'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['employment_status', 'department', 'position', 'employee_type']
    search_fields = [
        'employee_code',
        'person__first_name',
        'person__last_name',
        'person__email'
    ]
    ordering_fields = ['employee_code', 'hire_date', 'created_at']
    ordering = ['employee_code']

    def get_serializer_class(self):
        """Use different serializers for list and detail"""
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer

    def get_queryset(self):
        """Filter to show only active employees by default"""
        queryset = super().get_queryset()
        show_all = self.request.query_params.get('show_all', 'false')
        if show_all.lower() != 'true':
            queryset = queryset.filter(employment_status='ACTIVE')
        return queryset

    @action(detail=True, methods=['get'])
    def contracts(self, request, pk=None):
        """Get all contracts for employee"""
        employee = self.get_object()
        contracts = employee.contract_set.all()
        serializer = ContractSerializer(contracts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def leave_requests(self, request, pk=None):
        """Get all leave requests for employee"""
        employee = self.get_object()
        leave_requests = employee.leaverequest_set.all()
        serializer = LeaveRequestListSerializer(leave_requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def assets(self, request, pk=None):
        """Get all assigned assets for employee"""
        employee = self.get_object()
        assignments = employee.assetassignment_set.filter(
            returned_date__isnull=True
        )
        serializer = AssetAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate employee"""
        employee = self.get_object()
        termination_date = request.data.get('termination_date')

        if not termination_date:
            return Response(
                {'error': 'termination_date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        employee.employment_status = 'TERMINATED'
        employee.termination_date = termination_date
        employee.save()

        serializer = self.get_serializer(employee)
        return Response(serializer.data)


class ContractViewSet(viewsets.ModelViewSet):
    """API endpoint for Contract management"""
    queryset = Contract.objects.select_related('employee__person')
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['employee', 'contract_type', 'is_active']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']


class ShiftViewSet(viewsets.ModelViewSet):
    """API endpoint for Shift management"""
    queryset = Shift.objects.filter(is_active=True)
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'start_time']
    ordering = ['code']

    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """Get all assignments for shift"""
        shift = self.get_object()
        assignments = shift.shiftassignment_set.filter(end_date__isnull=True)
        serializer = ShiftAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


class ShiftAssignmentViewSet(viewsets.ModelViewSet):
    """API endpoint for ShiftAssignment management"""
    queryset = ShiftAssignment.objects.select_related(
        'employee__person', 'shift'
    )
    serializer_class = ShiftAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['employee', 'shift']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']


class AssetViewSet(viewsets.ModelViewSet):
    """API endpoint for Asset management"""
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['asset_type', 'status']
    search_fields = ['name', 'tag_number', 'serial_number']
    ordering_fields = ['tag_number', 'name', 'created_at']
    ordering = ['tag_number']

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get assignment history for asset"""
        asset = self.get_object()
        assignments = asset.assetassignment_set.all().order_by('-assigned_date')
        serializer = AssetAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign asset to employee"""
        asset = self.get_object()
        employee_id = request.data.get('employee_id')

        if not employee_id:
            return Response(
                {'error': 'employee_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            employee = Employee.objects.get(pk=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if asset is already assigned
        existing = asset.assetassignment_set.filter(
            returned_date__isnull=True
        ).first()

        if existing:
            return Response(
                {'error': 'Asset is already assigned'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create assignment
        assignment = AssetAssignment.objects.create(
            asset=asset,
            employee=employee,
            assigned_date=timezone.now().date(),
            condition_on_assignment=request.data.get('condition', 'GOOD')
        )

        # Update asset status
        asset.status = 'ASSIGNED'
        asset.save()

        serializer = AssetAssignmentSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AssetAssignmentViewSet(viewsets.ModelViewSet):
    """API endpoint for AssetAssignment management"""
    queryset = AssetAssignment.objects.select_related(
        'asset', 'employee__person'
    )
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['asset', 'employee']
    ordering_fields = ['assigned_date', 'returned_date']
    ordering = ['-assigned_date']


class LeaveTypeViewSet(viewsets.ModelViewSet):
    """API endpoint for LeaveType management"""
    queryset = LeaveType.objects.filter(is_active=True)
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']
    ordering = ['code']


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """API endpoint for LeaveRequest management"""
    queryset = LeaveRequest.objects.select_related(
        'employee__person', 'leave_type', 'approved_by'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['employee', 'leave_type', 'status']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        elif self.action == 'list':
            return LeaveRequestListSerializer
        return LeaveRequestDetailSerializer

    def get_queryset(self):
        """Filter to show user's own requests if not manager"""
        queryset = super().get_queryset()
        user = self.request.user

        # If user has employee record, show only their requests
        # unless they have specific permissions
        if hasattr(user, 'employee') and not user.has_perm('hr.view_all_leave_requests'):
            queryset = queryset.filter(employee__user=user)

        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve leave request"""
        leave_request = self.get_object()

        if leave_request.status != 'PENDING':
            return Response(
                {'error': 'Only pending requests can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get approver employee
        try:
            approver = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'User is not an employee'},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_request.status = 'APPROVED'
        leave_request.approved_by = approver
        leave_request.approved_at = timezone.now()
        leave_request.save()

        serializer = LeaveRequestDetailSerializer(leave_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject leave request"""
        leave_request = self.get_object()

        if leave_request.status != 'PENDING':
            return Response(
                {'error': 'Only pending requests can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        rejection_reason = request.data.get('rejection_reason')
        if not rejection_reason:
            return Response(
                {'error': 'rejection_reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get approver employee
        try:
            approver = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'User is not an employee'},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_request.status = 'REJECTED'
        leave_request.approved_by = approver
        leave_request.approved_at = timezone.now()
        leave_request.rejection_reason = rejection_reason
        leave_request.save()

        serializer = LeaveRequestDetailSerializer(leave_request)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get current user's leave requests"""
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'User is not an employee'},
                status=status.HTTP_404_NOT_FOUND
            )

        requests = self.get_queryset().filter(employee=employee)
        serializer = LeaveRequestListSerializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get leave requests pending approval for current user"""
        try:
            manager = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'User is not an employee'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get requests from employees reporting to this manager
        requests = self.get_queryset().filter(
            employee__report_to=manager,
            status='PENDING'
        )

        serializer = LeaveRequestListSerializer(requests, many=True)
        return Response(serializer.data)
