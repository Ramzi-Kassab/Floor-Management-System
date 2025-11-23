# urls.py - Updated for wizard-based employee creation system
from django.urls import path
from . import views_employee_wizard as views
from . import views_department
from . import views_position
from .views import leave_views, document_views, attendance_views, training_views
from .views import contract_views, shift_views, asset_views

app_name = "hr"

urlpatterns = [
    # ========== HR Dashboard ==========
    path("", views.hr_dashboard, name="dashboard"),
    path("api/stats/", views.dashboard_stats, name="dashboard_stats"),
    path("portal/", views.employee_portal, name="employee_portal"),
    
    # ========== Employee Creation Wizard ==========
    path("employee/wizard/", views.employee_wizard_start, name="employee_wizard_start"),
    path("employee/wizard/contact/", views.employee_wizard_contact, name="employee_wizard_contact"),
    path("employee/wizard/employee/", views.employee_wizard_employee, name="employee_wizard_employee"),
    path("employee/wizard/review/", views.employee_wizard_review, name="employee_wizard_review"),
    
    # ========== People Management ==========
    path("people/", views.people_list, name="people_list"),
    path("people/create/", views.person_create, name="person_create"),
    path("people/<int:pk>/", views.person_detail, name="person_detail"),
    path("people/<int:pk>/edit/", views.person_edit, name="person_edit"),
    path("people/<int:pk>/delete/", views.person_delete, name="person_delete"),
    path("people/search/", views.people_list, name="people_search"),  # Same as list with search params
    
    # ========== People APIs ==========
    path("api/people/search/", views.person_search_api, name="person_search_api"),
    path("api/people/<int:person_id>/", views.person_detail_api, name="person_detail_api"),
    path("api/people/create/", views.person_create_ajax, name="person_create_ajax"),
    path("api/people/<int:person_id>/contacts/", views.person_contacts_api, name="person_contacts_api"),
    path("api/contacts/save/", views.save_contacts_ajax, name="save_contacts_ajax"),
    path("api/convert-date/", views.convert_date, name="convert_date"),
    
    # ========== Employee Management ==========
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/active/", views.employee_active, name="employee_active"),
    path("employees/<int:pk>/", views.employee_detail, name="employee_detail"),
    path("employees/<int:pk>/edit/", views.employee_edit, name="employee_edit"),
    path("employees/import/", views.employee_import, name="employee_import"),
    path("employees/export/", views.employee_export, name="employee_export"),
    path("api/employee/save/", views.save_employee_ajax, name="save_employee_ajax"),
    
    # ========== Phone Management ==========
    path("phones/", views.phone_list, name="phone_list"),
    path("phones/bulk-add/", views.phone_bulk_add, name="phone_bulk_add"),
    
    # ========== Email Management ==========
    path("emails/", views.email_list, name="email_list"),
    path("emails/bulk-add/", views.email_bulk_add, name="email_bulk_add"),
    
    # ========== Address Management ==========
    path("addresses/", views.address_list, name="address_list"),
    path("addresses/add/", views.address_add, name="address_add"),
    path("addresses/<int:pk>/", views.address_detail, name="address_detail"),
    path("addresses/<int:pk>/edit/", views.address_edit, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    
    # ========== Departments ==========
    path("departments/", views_department.DepartmentListView.as_view(), name="department_list"),
    path("departments/create/", views_department.DepartmentCreateView.as_view(), name="department_create"),
    path("departments/<int:pk>/", views_department.DepartmentDetailView.as_view(), name="department_detail"),
    path("departments/<int:pk>/edit/", views_department.DepartmentUpdateView.as_view(), name="department_update"),
    path("departments/<int:pk>/delete/", views_department.DepartmentDeleteView.as_view(), name="department_delete"),
    
    # ========== Positions ==========
    path("positions/", views_position.PositionListView.as_view(), name="position_list"),
    path("positions/create/", views_position.PositionCreateView.as_view(), name="position_create"),
    path("positions/<int:pk>/", views_position.PositionDetailView.as_view(), name="position_detail"),
    path("positions/<int:pk>/edit/", views_position.PositionUpdateView.as_view(), name="position_update"),
    path("positions/<int:pk>/delete/", views_position.PositionDeleteView.as_view(), name="position_delete"),
    path("positions/api/", views_position.position_list_api, name="position_list_api"),

    # ========== API Endpoints for Wizard ==========
    path("api/departments/", views.department_list_api, name="department_list_api"),
    path("api/employees/", views.employee_list_api, name="employee_list_api"),

    # ========== Reports & Settings ==========
    path("reports/", views.reports, name="reports"),
    path("settings/", views.settings, name="settings"),

    # ========== Leave Management ==========
    # Leave Policies
    path("leave/policies/", leave_views.LeavePolicyListView.as_view(), name="leave_policy_list"),
    path("leave/policies/create/", leave_views.LeavePolicyCreateView.as_view(), name="leave_policy_create"),
    path("leave/policies/<int:pk>/", leave_views.LeavePolicyDetailView.as_view(), name="leave_policy_detail"),
    path("leave/policies/<int:pk>/edit/", leave_views.LeavePolicyUpdateView.as_view(), name="leave_policy_edit"),

    # Leave Balances
    path("leave/balances/", leave_views.leave_balance_dashboard, name="leave_balance_dashboard"),
    path("leave/balances/<int:pk>/adjust/", leave_views.leave_balance_adjust, name="leave_balance_adjust"),
    path("leave/balances/initialize/", leave_views.leave_balance_initialize, name="leave_balance_initialize"),

    # Leave Requests
    path("leave/requests/", leave_views.LeaveRequestListView.as_view(), name="leave_request_list"),
    path("leave/requests/create/", leave_views.LeaveRequestCreateView.as_view(), name="leave_request_create"),
    path("leave/requests/<int:pk>/", leave_views.LeaveRequestDetailView.as_view(), name="leave_request_detail"),
    path("leave/requests/<int:pk>/submit/", leave_views.leave_request_submit, name="leave_request_submit"),
    path("leave/requests/<int:pk>/approve/", leave_views.leave_request_approve, name="leave_request_approve"),
    path("leave/requests/<int:pk>/cancel/", leave_views.leave_request_cancel, name="leave_request_cancel"),

    # Leave Calendar & Dashboard
    path("leave/calendar/", leave_views.leave_calendar, name="leave_calendar"),
    path("leave/my-dashboard/", leave_views.my_leave_dashboard, name="my_leave_dashboard"),

    # ========== Employee Document Management ==========
    # Employee Self-Service Portal
    path("documents/my-documents/", document_views.my_documents_dashboard, name="my_documents_dashboard"),
    path("documents/upload/", document_views.employee_upload_document, name="employee_upload_document"),
    path("documents/<int:pk>/view/", document_views.employee_view_document, name="employee_view_document"),
    path("documents/<int:pk>/request-renewal/", document_views.employee_request_renewal, name="employee_request_renewal"),

    # HR Administrative Portal
    path("documents/hr/", document_views.hr_documents_dashboard, name="hr_documents_dashboard"),
    path("documents/hr/upload/", document_views.hr_upload_document, name="hr_upload_document"),
    path("documents/hr/expiry/", document_views.hr_expiry_dashboard, name="hr_expiry_dashboard"),
    path("documents/hr/<int:pk>/", document_views.hr_document_detail, name="hr_document_detail"),
    path("documents/hr/<int:pk>/verify/", document_views.hr_verify_document, name="hr_verify_document"),
    path("documents/hr/bulk-actions/", document_views.hr_bulk_actions, name="hr_bulk_actions"),
    path("documents/hr/print/", document_views.print_document_list, name="print_document_list"),

    # ========== Attendance & Overtime Management ==========
    # Attendance Dashboard & Records
    path("attendance/", attendance_views.attendance_dashboard, name="attendance_dashboard"),
    path("attendance/list/", attendance_views.attendance_list, name="attendance_list"),
    path("attendance/entry/", attendance_views.attendance_entry, name="attendance_entry"),
    path("attendance/import/", attendance_views.punch_machine_import, name="punch_machine_import"),
    path("attendance/export/", attendance_views.export_attendance_csv, name="export_attendance_csv"),
    path("attendance/reports/", attendance_views.attendance_report, name="attendance_report"),

    # Overtime Requests
    path("overtime/", attendance_views.overtime_request_list, name="overtime_request_list"),
    path("overtime/request/", attendance_views.overtime_request_create, name="overtime_request_create"),
    path("overtime/<int:pk>/", attendance_views.overtime_request_detail, name="overtime_request_detail"),
    path("overtime/<int:pk>/approve/", attendance_views.overtime_request_approve, name="overtime_request_approve"),

    # Delay/Late Arrival Management
    path("delays/", attendance_views.delay_incident_list, name="delay_incident_list"),
    path("delays/report/", attendance_views.delay_incident_report, name="delay_incident_report"),
    path("delays/<int:pk>/review/", attendance_views.delay_incident_review, name="delay_incident_review"),

    # ========== Training & Development Management ==========
    # Training Programs
    path("training/programs/", training_views.TrainingProgramListView.as_view(), name="training_program_list"),
    path("training/programs/create/", training_views.TrainingProgramCreateView.as_view(), name="training_program_create"),
    path("training/programs/<int:pk>/", training_views.TrainingProgramDetailView.as_view(), name="training_program_detail"),
    path("training/programs/<int:pk>/edit/", training_views.TrainingProgramUpdateView.as_view(), name="training_program_edit"),

    # Training Sessions
    path("training/sessions/", training_views.TrainingSessionListView.as_view(), name="training_session_list"),
    path("training/sessions/create/", training_views.TrainingSessionCreateView.as_view(), name="training_session_create"),
    path("training/sessions/<int:pk>/", training_views.TrainingSessionDetailView.as_view(), name="training_session_detail"),
    path("training/sessions/<int:pk>/edit/", training_views.TrainingSessionUpdateView.as_view(), name="training_session_edit"),
    path("training/sessions/<int:session_id>/enroll/", training_views.enroll_employees, name="training_enroll"),

    # Employee Training
    path("training/my-training/", training_views.my_training_dashboard, name="my_training_dashboard"),
    path("training/complete/<int:pk>/", training_views.complete_training, name="training_complete"),
    path("training/feedback/<int:pk>/", training_views.submit_feedback, name="training_feedback"),

    # ========== Contract Management ==========
    # Contract Dashboard & List
    path("contracts/", contract_views.ContractListView.as_view(), name="contract_list"),
    path("contracts/dashboard/", contract_views.contract_dashboard, name="contract_dashboard"),

    # Contract CRUD
    path("contracts/create/", contract_views.ContractCreateView.as_view(), name="contract_create"),
    path("contracts/<int:pk>/", contract_views.ContractDetailView.as_view(), name="contract_detail"),
    path("contracts/<int:pk>/edit/", contract_views.ContractUpdateView.as_view(), name="contract_edit"),

    # Contract Actions
    path("contracts/<int:pk>/renew/", contract_views.contract_renew, name="contract_renew"),
    path("contracts/<int:pk>/terminate/", contract_views.contract_terminate, name="contract_terminate"),

    # Contract Reports
    path("contracts/report/", contract_views.contract_report, name="contract_report"),
    path("contracts/export/", contract_views.export_contracts_csv, name="export_contracts_csv"),

    # ========== Shift Management ==========
    # Shift Templates
    path("shifts/templates/", shift_views.ShiftTemplateListView.as_view(), name="shift_template_list"),
    path("shifts/templates/create/", shift_views.ShiftTemplateCreateView.as_view(), name="shift_template_create"),
    path("shifts/templates/<int:pk>/", shift_views.ShiftTemplateDetailView.as_view(), name="shift_template_detail"),
    path("shifts/templates/<int:pk>/edit/", shift_views.ShiftTemplateUpdateView.as_view(), name="shift_template_edit"),

    # Shift Assignments
    path("shifts/assignments/", shift_views.ShiftAssignmentListView.as_view(), name="shift_assignment_list"),
    path("shifts/assignments/create/", shift_views.ShiftAssignmentCreateView.as_view(), name="shift_assignment_create"),
    path("shifts/assignments/<int:pk>/", shift_views.ShiftAssignmentDetailView.as_view(), name="shift_assignment_detail"),
    path("shifts/assignments/<int:pk>/edit/", shift_views.ShiftAssignmentUpdateView.as_view(), name="shift_assignment_edit"),
    path("shifts/assignments/<int:pk>/end/", shift_views.end_shift_assignment, name="shift_assignment_end"),

    # Shift Schedule
    path("shifts/schedule/", shift_views.shift_schedule, name="shift_schedule"),

    # Shift APIs
    path("api/shifts/templates/", shift_views.shift_template_api, name="shift_template_api"),
    path("api/employees/<int:employee_id>/shift/", shift_views.employee_current_shift, name="employee_current_shift"),

    # ========== Asset Management ==========
    # Asset Types
    path("assets/types/", asset_views.AssetTypeListView.as_view(), name="asset_type_list"),
    path("assets/types/create/", asset_views.AssetTypeCreateView.as_view(), name="asset_type_create"),
    path("assets/types/<int:pk>/edit/", asset_views.AssetTypeUpdateView.as_view(), name="asset_type_edit"),

    # Assets
    path("assets/", asset_views.AssetListView.as_view(), name="asset_list"),
    path("assets/dashboard/", asset_views.asset_dashboard, name="asset_dashboard"),
    path("assets/create/", asset_views.AssetCreateView.as_view(), name="asset_create"),
    path("assets/<int:pk>/", asset_views.AssetDetailView.as_view(), name="asset_detail"),
    path("assets/<int:pk>/edit/", asset_views.AssetUpdateView.as_view(), name="asset_edit"),
    path("assets/export/", asset_views.export_assets_csv, name="export_assets_csv"),

    # Asset Assignments
    path("assets/assignments/", asset_views.AssetAssignmentListView.as_view(), name="asset_assignment_list"),
    path("assets/assignments/create/", asset_views.AssetAssignmentCreateView.as_view(), name="asset_assignment_create"),
    path("assets/assignments/<int:pk>/", asset_views.AssetAssignmentDetailView.as_view(), name="asset_assignment_detail"),
    path("assets/assignments/<int:pk>/return/", asset_views.return_asset, name="return_asset"),

    # Asset APIs
    path("api/assets/search/", asset_views.asset_search_api, name="asset_search_api"),
    path("api/employees/<int:employee_id>/assets/", asset_views.employee_assets_api, name="employee_assets_api"),

    # ========== Legacy/Deprecated URLs (redirect to new system) ==========
    path("employees/create/", views.employee_wizard_start, name="employee_create"),  # Redirect to wizard
    path("employees/setup/new/", views.employee_wizard_start, name="employee_setup_new"),
]
