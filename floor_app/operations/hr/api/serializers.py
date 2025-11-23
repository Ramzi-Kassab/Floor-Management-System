"""
REST API Serializers for HR Module
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from floor_app.operations.hr.models import (
    Person, Department, Position, Employee, Contract,
    Shift, ShiftAssignment, Asset, AssetAssignment,
    LeaveType, LeaveRequest
)

User = get_user_model()


class PersonSerializer(serializers.ModelSerializer):
    """Serializer for Person model"""
    age = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Person
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'age', 'gender', 'marital_status',
            'email', 'phone', 'mobile', 'address',
            'city', 'state', 'country', 'postal_code',
            'emergency_contact_name', 'emergency_contact_phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'code', 'name', 'description',
            'employee_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_count(self, obj):
        """Get count of employees in department"""
        return obj.employee_set.filter(employment_status='ACTIVE').count()


class PositionSerializer(serializers.ModelSerializer):
    """Serializer for Position model"""
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Position
        fields = [
            'id', 'code', 'title', 'description',
            'employee_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_employee_count(self, obj):
        """Get count of employees in position"""
        return obj.employee_set.filter(employment_status='ACTIVE').count()


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for Employee list view (minimal data)"""
    person_name = serializers.CharField(source='person.full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_code', 'person_name',
            'department_name', 'position_title',
            'employment_status', 'hire_date'
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Serializer for Employee detail view (complete data)"""
    person = PersonSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    position = PositionSerializer(read_only=True)
    report_to_name = serializers.CharField(
        source='report_to.person.full_name',
        read_only=True,
        allow_null=True
    )

    # Write fields for relationships
    person_id = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.all(),
        source='person',
        write_only=True
    )
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True
    )
    position_id = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.all(),
        source='position',
        write_only=True
    )
    report_to_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        source='report_to',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_code', 'person', 'person_id',
            'department', 'department_id', 'position', 'position_id',
            'report_to', 'report_to_id', 'report_to_name',
            'hire_date', 'termination_date', 'employment_status',
            'employee_type', 'work_location', 'user',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for Contract model"""
    employee_name = serializers.CharField(
        source='employee.person.full_name',
        read_only=True
    )
    employee_code = serializers.CharField(
        source='employee.employee_code',
        read_only=True
    )

    class Meta:
        model = Contract
        fields = [
            'id', 'employee', 'employee_name', 'employee_code',
            'contract_type', 'start_date', 'end_date',
            'salary', 'currency', 'payment_frequency',
            'probation_period', 'notice_period',
            'benefits', 'terms', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """Validate contract dates"""
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError(
                    "End date must be after start date"
                )
        return data


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift model"""
    assigned_employees = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = [
            'id', 'code', 'name', 'description',
            'start_time', 'end_time', 'color',
            'assigned_employees', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_assigned_employees(self, obj):
        """Get count of assigned employees"""
        return obj.shiftassignment_set.filter(
            end_date__isnull=True
        ).count()


class ShiftAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for ShiftAssignment model"""
    employee_name = serializers.CharField(
        source='employee.person.full_name',
        read_only=True
    )
    shift_name = serializers.CharField(source='shift.name', read_only=True)

    class Meta:
        model = ShiftAssignment
        fields = [
            'id', 'employee', 'employee_name',
            'shift', 'shift_name',
            'start_date', 'end_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AssetSerializer(serializers.ModelSerializer):
    """Serializer for Asset model"""
    assigned_to = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            'id', 'asset_type', 'name', 'tag_number',
            'serial_number', 'description', 'manufacturer',
            'model', 'purchase_date', 'purchase_cost',
            'warranty_expiry', 'status', 'location',
            'assigned_to', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_assigned_to(self, obj):
        """Get currently assigned employee"""
        assignment = obj.assetassignment_set.filter(
            returned_date__isnull=True
        ).first()
        if assignment:
            return {
                'employee_id': assignment.employee.id,
                'employee_name': assignment.employee.person.full_name,
                'employee_code': assignment.employee.employee_code,
                'assigned_date': assignment.assigned_date
            }
        return None


class AssetAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for AssetAssignment model"""
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    employee_name = serializers.CharField(
        source='employee.person.full_name',
        read_only=True
    )

    class Meta:
        model = AssetAssignment
        fields = [
            'id', 'asset', 'asset_name', 'employee', 'employee_name',
            'assigned_date', 'assigned_by', 'condition_on_assignment',
            'returned_date', 'returned_to', 'return_condition',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class LeaveTypeSerializer(serializers.ModelSerializer):
    """Serializer for LeaveType model"""

    class Meta:
        model = LeaveType
        fields = [
            'id', 'code', 'name', 'description',
            'days_per_year', 'requires_approval',
            'can_be_carried_forward', 'max_consecutive_days',
            'color', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class LeaveRequestListSerializer(serializers.ModelSerializer):
    """Serializer for LeaveRequest list view"""
    employee_name = serializers.CharField(
        source='employee.person.full_name',
        read_only=True
    )
    leave_type_name = serializers.CharField(
        source='leave_type.name',
        read_only=True
    )
    days = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name',
            'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'days',
            'status', 'created_at'
        ]

    def get_days(self, obj):
        """Calculate number of days"""
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days + 1
        return 0


class LeaveRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer for LeaveRequest detail view"""
    employee_name = serializers.CharField(
        source='employee.person.full_name',
        read_only=True
    )
    leave_type_name = serializers.CharField(
        source='leave_type.name',
        read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.person.full_name',
        read_only=True,
        allow_null=True
    )
    days = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name',
            'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'days',
            'reason', 'status', 'approved_by',
            'approved_by_name', 'approved_at',
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'approved_by',
            'approved_at'
        ]

    def get_days(self, obj):
        """Calculate number of days"""
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days + 1
        return 0


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating leave requests"""

    class Meta:
        model = LeaveRequest
        fields = [
            'employee', 'leave_type',
            'start_date', 'end_date', 'reason'
        ]

    def validate(self, data):
        """Validate leave request"""
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError(
                "End date must be after start date"
            )

        # Check for overlapping leave requests
        overlapping = LeaveRequest.objects.filter(
            employee=data['employee'],
            status__in=['PENDING', 'APPROVED'],
            start_date__lte=data['end_date'],
            end_date__gte=data['start_date']
        )

        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)

        if overlapping.exists():
            raise serializers.ValidationError(
                "Leave request overlaps with existing request"
            )

        return data

    def create(self, validated_data):
        """Create leave request with PENDING status"""
        validated_data['status'] = 'PENDING'
        return super().create(validated_data)
