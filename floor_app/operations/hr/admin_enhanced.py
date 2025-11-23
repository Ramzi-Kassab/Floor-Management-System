"""
Enhanced HR Admin Configuration with Advanced Features

This module provides enhanced Django admin configurations including:
- Custom actions (bulk operations)
- Inline editing
- Advanced filtering
- Export functionality
- Custom list displays with calculated fields
- Improved UX
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from .models import (
    Person, Department, Position, Employee, Contract,
    Shift, ShiftAssignment, Asset, AssetAssignment,
    LeaveType, LeaveRequest
)


# ============================================================================
# RESOURCES FOR IMPORT/EXPORT
# ============================================================================

class PersonResource(resources.ModelResource):
    """Resource for importing/exporting Person data"""
    class Meta:
        model = Person
        fields = ('id', 'first_name', 'last_name', 'date_of_birth',
                 'gender', 'email', 'phone', 'city', 'country')
        export_order = fields


class EmployeeResource(resources.ModelResource):
    """Resource for importing/exporting Employee data"""
    person_name = resources.Field()
    department_name = resources.Field()
    position_title = resources.Field()

    class Meta:
        model = Employee
        fields = ('id', 'employee_code', 'person_name', 'department_name',
                 'position_title', 'hire_date', 'employment_status')

    def dehydrate_person_name(self, employee):
        return employee.person.full_name

    def dehydrate_department_name(self, employee):
        return employee.department.name if employee.department else ''

    def dehydrate_position_title(self, employee):
        return employee.position.title if employee.position else ''


# ============================================================================
# INLINE ADMIN CLASSES
# ============================================================================

class ContractInline(admin.TabularInline):
    """Inline for employee contracts"""
    model = Contract
    extra = 0
    fields = ['contract_type', 'start_date', 'end_date', 'salary', 'is_active']
    readonly_fields = []
    show_change_link = True


class ShiftAssignmentInline(admin.TabularInline):
    """Inline for shift assignments"""
    model = ShiftAssignment
    extra = 0
    fields = ['shift', 'start_date', 'end_date']
    show_change_link = True


class AssetAssignmentInline(admin.TabularInline):
    """Inline for asset assignments"""
    model = AssetAssignment
    extra = 0
    fields = ['asset', 'assigned_date', 'returned_date', 'condition_on_assignment']
    readonly_fields = ['assigned_date']
    show_change_link = True


class LeaveRequestInline(admin.TabularInline):
    """Inline for leave requests"""
    model = LeaveRequest
    extra = 0
    fields = ['leave_type', 'start_date', 'end_date', 'status']
    readonly_fields = ['status']
    show_change_link = True
    max_num = 5


# ============================================================================
# ENHANCED ADMIN CLASSES
# ============================================================================

@admin.register(Person)
class PersonAdminEnhanced(ImportExportModelAdmin):
    """Enhanced Person admin with import/export"""
    resource_class = PersonResource

    list_display = [
        'full_name_link', 'email', 'phone', 'age_display',
        'gender', 'city', 'country', 'has_emergency_contact'
    ]
    list_filter = ['gender', 'marital_status', 'country', 'created_at']
    search_fields = [
        'first_name', 'last_name', 'email', 'phone',
        'mobile', 'city', 'country'
    ]
    readonly_fields = ['created_at', 'updated_at', 'age']

    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'age',
                      'gender', 'marital_status')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'mobile', 'address',
                      'city', 'state', 'country', 'postal_code')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def full_name_link(self, obj):
        """Link to person detail"""
        url = reverse('admin:hr_person_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, obj.full_name)
    full_name_link.short_description = 'Full Name'

    def age_display(self, obj):
        """Display age with color coding"""
        age = obj.age
        if age:
            color = 'green' if 18 <= age <= 65 else 'orange'
            return format_html('<span style="color: {};">{}</span>', color, age)
        return '-'
    age_display.short_description = 'Age'

    def has_emergency_contact(self, obj):
        """Check if emergency contact is set"""
        has_contact = bool(obj.emergency_contact_name and obj.emergency_contact_phone)
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if has_contact else 'red',
            '✓' if has_contact else '✗'
        )
    has_emergency_contact.short_description = 'Emergency Contact'

    actions = ['export_selected_persons']

    def export_selected_persons(self, request, queryset):
        """Custom export action"""
        # This leverages the import_export functionality
        pass
    export_selected_persons.short_description = "Export selected persons"


@admin.register(Department)
class DepartmentAdminEnhanced(admin.ModelAdmin):
    """Enhanced Department admin"""
    list_display = [
        'code', 'name', 'active_employees_count',
        'is_active_display', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'active_employees_count']

    fieldsets = (
        ('Department Information', {
            'fields': ('code', 'name', 'description', 'is_active')
        }),
        ('Statistics', {
            'fields': ('active_employees_count',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def active_employees_count(self, obj):
        """Count active employees in department"""
        return obj.employee_set.filter(employment_status='ACTIVE').count()
    active_employees_count.short_description = 'Active Employees'

    def is_active_display(self, obj):
        """Display active status with icon"""
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.is_active else 'red',
            '✓ Active' if obj.is_active else '✗ Inactive'
        )
    is_active_display.short_description = 'Status'

    actions = ['activate_departments', 'deactivate_departments']

    def activate_departments(self, request, queryset):
        """Activate selected departments"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} departments activated.')
    activate_departments.short_description = "Activate selected departments"

    def deactivate_departments(self, request, queryset):
        """Deactivate selected departments"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} departments deactivated.')
    deactivate_departments.short_description = "Deactivate selected departments"


@admin.register(Employee)
class EmployeeAdminEnhanced(ImportExportModelAdmin):
    """Enhanced Employee admin with inlines and actions"""
    resource_class = EmployeeResource

    list_display = [
        'employee_code_link', 'person_name', 'department',
        'position', 'employment_status_display', 'hire_date',
        'service_duration', 'has_active_contract'
    ]
    list_filter = [
        'employment_status', 'employee_type', 'department',
        'position', 'hire_date'
    ]
    search_fields = [
        'employee_code', 'person__first_name',
        'person__last_name', 'person__email'
    ]
    readonly_fields = ['created_at', 'updated_at', 'service_duration']
    date_hierarchy = 'hire_date'

    inlines = [ContractInline, ShiftAssignmentInline, AssetAssignmentInline, LeaveRequestInline]

    fieldsets = (
        ('Employee Information', {
            'fields': ('employee_code', 'person', 'user')
        }),
        ('Employment Details', {
            'fields': ('department', 'position', 'report_to',
                      'employment_status', 'employee_type')
        }),
        ('Dates', {
            'fields': ('hire_date', 'termination_date', 'service_duration')
        }),
        ('Work Details', {
            'fields': ('work_location',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def employee_code_link(self, obj):
        """Link to employee detail"""
        url = reverse('admin:hr_employee_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, obj.employee_code)
    employee_code_link.short_description = 'Employee Code'

    def person_name(self, obj):
        """Display person full name"""
        return obj.person.full_name if obj.person else '-'
    person_name.short_description = 'Name'

    def employment_status_display(self, obj):
        """Display employment status with color"""
        colors = {
            'ACTIVE': 'green',
            'ON_LEAVE': 'orange',
            'TERMINATED': 'red',
            'SUSPENDED': 'red'
        }
        color = colors.get(obj.employment_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_employment_status_display()
        )
    employment_status_display.short_description = 'Status'

    def service_duration(self, obj):
        """Calculate service duration"""
        if obj.hire_date:
            end_date = obj.termination_date or timezone.now().date()
            delta = end_date - obj.hire_date
            years = delta.days // 365
            months = (delta.days % 365) // 30
            return f"{years}y {months}m"
        return '-'
    service_duration.short_description = 'Service Duration'

    def has_active_contract(self, obj):
        """Check if employee has active contract"""
        has_contract = obj.contract_set.filter(is_active=True).exists()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if has_contract else 'red',
            '✓' if has_contract else '✗'
        )
    has_active_contract.short_description = 'Active Contract'

    actions = [
        'terminate_employees',
        'activate_employees',
        'export_employee_list'
    ]

    def terminate_employees(self, request, queryset):
        """Terminate selected employees"""
        queryset.update(
            employment_status='TERMINATED',
            termination_date=timezone.now().date()
        )
        self.message_user(request, f'{queryset.count()} employees terminated.')
    terminate_employees.short_description = "Terminate selected employees"

    def activate_employees(self, request, queryset):
        """Activate selected employees"""
        queryset.update(employment_status='ACTIVE', termination_date=None)
        self.message_user(request, f'{queryset.count()} employees activated.')
    activate_employees.short_description = "Activate selected employees"


@admin.register(LeaveRequest)
class LeaveRequestAdminEnhanced(admin.ModelAdmin):
    """Enhanced Leave Request admin"""
    list_display = [
        'employee_name', 'leave_type', 'start_date',
        'end_date', 'total_days', 'status_display',
        'approved_by_name', 'created_at'
    ]
    list_filter = ['status', 'leave_type', 'start_date', 'created_at']
    search_fields = [
        'employee__employee_code',
        'employee__person__first_name',
        'employee__person__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'total_days']
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Leave Request Information', {
            'fields': ('employee', 'leave_type', 'start_date',
                      'end_date', 'total_days', 'reason')
        }),
        ('Approval Information', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def employee_name(self, obj):
        """Display employee name"""
        return obj.employee.person.full_name
    employee_name.short_description = 'Employee'

    def status_display(self, obj):
        """Display status with color"""
        colors = {
            'PENDING': 'orange',
            'APPROVED': 'green',
            'REJECTED': 'red',
            'CANCELLED': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def approved_by_name(self, obj):
        """Display approver name"""
        if obj.approved_by:
            return obj.approved_by.person.full_name
        return '-'
    approved_by_name.short_description = 'Approved By'

    def total_days(self, obj):
        """Calculate total days"""
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days + 1
        return 0
    total_days.short_description = 'Days'

    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        """Approve selected leave requests"""
        pending = queryset.filter(status='PENDING')
        updated = pending.update(
            status='APPROVED',
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} requests approved.')
    approve_requests.short_description = "Approve selected requests"

    def reject_requests(self, request, queryset):
        """Reject selected leave requests"""
        pending = queryset.filter(status='PENDING')
        updated = pending.update(
            status='REJECTED',
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} requests rejected.')
    reject_requests.short_description = "Reject selected requests"


@admin.register(Asset)
class AssetAdminEnhanced(admin.ModelAdmin):
    """Enhanced Asset admin"""
    list_display = [
        'tag_number', 'name', 'asset_type', 'status_display',
        'current_assignment', 'purchase_date', 'warranty_status'
    ]
    list_filter = ['asset_type', 'status', 'purchase_date']
    search_fields = ['tag_number', 'name', 'serial_number']
    readonly_fields = ['created_at', 'updated_at']

    inlines = [AssetAssignmentInline]

    def status_display(self, obj):
        """Display status with color"""
        colors = {
            'AVAILABLE': 'green',
            'ASSIGNED': 'blue',
            'MAINTENANCE': 'orange',
            'RETIRED': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def current_assignment(self, obj):
        """Show current assignment"""
        assignment = obj.assetassignment_set.filter(
            returned_date__isnull=True
        ).first()
        if assignment:
            return f"{assignment.employee.person.full_name}"
        return '-'
    current_assignment.short_description = 'Assigned To'

    def warranty_status(self, obj):
        """Show warranty status"""
        if obj.warranty_expiry:
            is_valid = obj.warranty_expiry >= timezone.now().date()
            return format_html(
                '<span style="color: {};">{}</span>',
                'green' if is_valid else 'red',
                'Valid' if is_valid else 'Expired'
            )
        return '-'
    warranty_status.short_description = 'Warranty'

    actions = ['mark_as_available', 'mark_as_maintenance']

    def mark_as_available(self, request, queryset):
        """Mark assets as available"""
        updated = queryset.update(status='AVAILABLE')
        self.message_user(request, f'{updated} assets marked as available.')
    mark_as_available.short_description = "Mark as available"

    def mark_as_maintenance(self, request, queryset):
        """Mark assets as in maintenance"""
        updated = queryset.update(status='MAINTENANCE')
        self.message_user(request, f'{updated} assets marked as maintenance.')
    mark_as_maintenance.short_description = "Mark as maintenance"
