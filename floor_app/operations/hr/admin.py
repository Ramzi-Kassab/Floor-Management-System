"""
HR Admin Configuration

Admin interface configuration for all HR models.
"""
from django.contrib import admin
from .models import (
    # People & Contact
    Person,
    PhoneNumber,
    EmailAddress,
    # Employee Management
    HREmployee,
    Department,
    Position,
    # Qualifications
    Qualification,
    # Leave Management
    LeaveType,
    LeavePolicy,
    LeaveBalance,
    LeaveRequest,
    # Attendance
    AttendanceRecord,
    OvertimeRequest,
    AttendanceSummary,
    AttendanceConfiguration,
    OvertimeConfiguration,
    DelayIncident,
    # Training
    TrainingProgram,
    TrainingSession,
    EmployeeTraining,
    SkillMatrix,
    # Documents
    EmployeeDocument,
    DocumentRenewal,
    ExpiryAlert,
    # Contracts & Shifts
    HRContract,
    HRShiftTemplate,
    ShiftAssignment,
    # Assets
    AssetType,
    HRAsset,
    AssetAssignment,
)


# ============================================================================
# PEOPLE & CONTACT
# ============================================================================

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'national_id', 'nationality', 'date_of_birth', 'created_at']
    list_filter = ['gender', 'nationality', 'marital_status']
    search_fields = ['first_name', 'last_name', 'national_id', 'passport_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'gender', 'date_of_birth')
        }),
        ('Identification', {
            'fields': ('national_id', 'passport_number', 'nationality')
        }),
        ('Contact', {
            'fields': ('marital_status', 'emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ['person', 'phone_number', 'phone_type', 'is_primary', 'created_at']
    list_filter = ['phone_type', 'is_primary']
    search_fields = ['person__first_name', 'person__last_name', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmailAddress)
class EmailAddressAdmin(admin.ModelAdmin):
    list_display = ['person', 'email', 'email_type', 'is_primary', 'created_at']
    list_filter = ['email_type', 'is_primary']
    search_fields = ['person__first_name', 'person__last_name', 'email']
    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# EMPLOYEE MANAGEMENT
# ============================================================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'department', 'level', 'is_active', 'created_at']
    list_filter = ['department', 'level', 'is_active']
    search_fields = ['code', 'title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HREmployee)
class HREmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_code', 'person', 'department', 'position', 'employment_status', 'hire_date']
    list_filter = ['employment_status', 'department', 'employee_type', 'is_active']
    search_fields = ['employee_code', 'person__first_name', 'person__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'hire_date'
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee_code', 'person', 'user')
        }),
        ('Employment Details', {
            'fields': ('department', 'position', 'employment_status', 'employee_type', 'hire_date', 'termination_date')
        }),
        ('Work Details', {
            'fields': ('work_location', 'shift', 'probation_end_date', 'contract_end_date')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'qualification_type', 'degree_title', 'institution', 'year_obtained']
    list_filter = ['qualification_type', 'year_obtained']
    search_fields = ['employee__employee_code', 'employee__person__first_name', 'degree_title', 'institution']
    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# LEAVE MANAGEMENT
# ============================================================================

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_paid', 'requires_approval', 'is_active']
    list_filter = ['is_paid', 'requires_approval', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = ['leave_type', 'employee_type', 'annual_entitlement', 'is_active']
    list_filter = ['leave_type', 'employee_type', 'is_active']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'total_entitlement', 'used_days', 'available_days']
    list_filter = ['leave_type', 'year']
    search_fields = ['employee__employee_code', 'employee__person__first_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'status', 'created_at']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__employee_code', 'employee__person__first_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


# ============================================================================
# ATTENDANCE
# ============================================================================

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in_time', 'check_out_time', 'status', 'work_hours']
    list_filter = ['status', 'date']
    search_fields = ['employee__employee_code', 'employee__person__first_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(OvertimeRequest)
class OvertimeRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'overtime_type', 'hours', 'status', 'created_at']
    list_filter = ['status', 'overtime_type', 'date']
    search_fields = ['employee__employee_code', 'employee__person__first_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'year', 'working_days', 'present_days', 'absent_days', 'late_days']
    list_filter = ['year', 'month']
    search_fields = ['employee__employee_code', 'employee__person__first_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AttendanceConfiguration)
class AttendanceConfigurationAdmin(admin.ModelAdmin):
    list_display = ['department', 'work_start_time', 'work_end_time', 'grace_period_minutes', 'is_active']
    list_filter = ['is_active']
    search_fields = ['department__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(OvertimeConfiguration)
class OvertimeConfigurationAdmin(admin.ModelAdmin):
    list_display = ['employee_type', 'overtime_type', 'rate_multiplier', 'requires_approval', 'is_active']
    list_filter = ['employee_type', 'overtime_type', 'is_active']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DelayIncident)
class DelayIncidentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'scheduled_time', 'actual_time', 'delay_minutes', 'delay_reason']
    list_filter = ['delay_reason', 'date']
    search_fields = ['employee__employee_code', 'employee__person__first_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


# ============================================================================
# TRAINING
# ============================================================================

@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'training_type', 'duration_hours', 'is_mandatory', 'is_active']
    list_filter = ['training_type', 'is_mandatory', 'is_active']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['program', 'session_code', 'start_date', 'end_date', 'trainer', 'max_participants', 'status']
    list_filter = ['status', 'start_date']
    search_fields = ['session_code', 'program__name', 'trainer']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(EmployeeTraining)
class EmployeeTrainingAdmin(admin.ModelAdmin):
    list_display = ['employee', 'session', 'enrollment_date', 'completion_date', 'status', 'score']
    list_filter = ['status', 'enrollment_date']
    search_fields = ['employee__employee_code', 'employee__person__first_name', 'session__session_code']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'enrollment_date'


@admin.register(SkillMatrix)
class SkillMatrixAdmin(admin.ModelAdmin):
    list_display = ['employee', 'skill_name', 'proficiency_level', 'years_experience', 'last_assessed_date']
    list_filter = ['proficiency_level']
    search_fields = ['employee__employee_code', 'skill_name']
    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# DOCUMENTS
# ============================================================================

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'document_type', 'document_number', 'issue_date', 'expiry_date', 'status']
    list_filter = ['document_type', 'status', 'issue_date']
    search_fields = ['employee__employee_code', 'document_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'issue_date'


@admin.register(DocumentRenewal)
class DocumentRenewalAdmin(admin.ModelAdmin):
    list_display = ['document', 'renewal_date', 'new_expiry_date', 'status', 'created_at']
    list_filter = ['status', 'renewal_date']
    search_fields = ['document__document_number', 'document__employee__employee_code']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'renewal_date'


@admin.register(ExpiryAlert)
class ExpiryAlertAdmin(admin.ModelAdmin):
    list_display = ['document', 'alert_date', 'days_before_expiry', 'notification_sent', 'created_at']
    list_filter = ['notification_sent', 'alert_date']
    search_fields = ['document__document_number', 'document__employee__employee_code']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'alert_date'


# ============================================================================
# CONTRACTS & SHIFTS
# ============================================================================

@admin.register(HRContract)
class HRContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'employee', 'contract_type', 'start_date', 'end_date', 'is_current', 'total_compensation']
    list_filter = ['contract_type', 'is_current', 'start_date']
    search_fields = ['contract_number', 'employee__employee_code', 'employee__person__first_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'
    fieldsets = (
        ('Contract Details', {
            'fields': ('employee', 'contract_number', 'contract_type', 'start_date', 'end_date', 'is_current')
        }),
        ('Compensation (Finance)', {
            'fields': ('basic_salary', 'housing_allowance', 'transport_allowance', 'other_allowances', 'currency'),
            'classes': ('collapse',)
        }),
        ('Terms', {
            'fields': ('probation_period_months', 'notice_period_days', 'work_hours_per_week', 'annual_leave_days')
        }),
        ('Document', {
            'fields': ('contract_file', 'notes')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HRShiftTemplate)
class HRShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'start_time', 'end_time', 'duration_hours', 'is_night_shift', 'is_active']
    list_filter = ['is_night_shift', 'is_active', 'department']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'shift_template', 'start_date', 'end_date', 'is_active', 'is_current']
    list_filter = ['is_active', 'start_date', 'shift_template']
    search_fields = ['employee__employee_code', 'employee__person__first_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


# ============================================================================
# ASSETS
# ============================================================================

@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'requires_serial_number', 'requires_maintenance', 'is_active']
    list_filter = ['category', 'requires_serial_number', 'requires_maintenance', 'is_active']
    search_fields = ['code', 'name', 'category']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HRAsset)
class HRAssetAdmin(admin.ModelAdmin):
    list_display = ['asset_tag', 'name', 'asset_type', 'status', 'condition', 'current_location', 'is_available']
    list_filter = ['asset_type', 'status', 'condition', 'purchase_date']
    search_fields = ['asset_tag', 'name', 'serial_number', 'manufacturer', 'model']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'purchase_date'
    fieldsets = (
        ('Asset Identification', {
            'fields': ('asset_tag', 'asset_type', 'name', 'serial_number')
        }),
        ('Details', {
            'fields': ('manufacturer', 'model', 'specifications')
        }),
        ('Purchase Information', {
            'fields': ('purchase_date', 'purchase_cost', 'currency', 'supplier', 'warranty_expiry_date'),
            'classes': ('collapse',)
        }),
        ('Status & Location', {
            'fields': ('status', 'condition', 'current_location', 'cost_center')
        }),
        ('Maintenance', {
            'fields': ('last_maintenance_date', 'next_maintenance_date'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ['asset', 'employee', 'assignment_date', 'expected_return_date', 'actual_return_date', 'status', 'is_active']
    list_filter = ['status', 'assignment_date', 'employee_acknowledged']
    search_fields = ['asset__asset_tag', 'asset__name', 'employee__employee_code']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'assignment_date'
    fieldsets = (
        ('Assignment', {
            'fields': ('asset', 'employee', 'assignment_date', 'expected_return_date', 'actual_return_date', 'status')
        }),
        ('Condition Tracking', {
            'fields': ('condition_at_assignment', 'condition_at_return')
        }),
        ('Notes', {
            'fields': ('assignment_notes', 'return_notes')
        }),
        ('Acknowledgment', {
            'fields': ('employee_acknowledged', 'acknowledgment_signature'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'assigned_by', 'returned_by'),
            'classes': ('collapse',)
        }),
    )
