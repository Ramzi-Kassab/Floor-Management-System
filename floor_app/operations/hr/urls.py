# urls.py - Updated for wizard-based employee creation system
from django.urls import path
from . import views_employee_wizard as views
from . import views_department

app_name = "hr"

urlpatterns = [
    # ========== HR Dashboard ==========
    path("", views.hr_dashboard, name="dashboard"),
    path("api/stats/", views.dashboard_stats, name="dashboard_stats"),
    
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
    path("positions/", views.position_list, name="position_list"),  # You'll need to implement these
    path("positions/api/", views.position_list_api, name="position_list_api"),

    # ========== API Endpoints for Wizard ==========
    path("api/departments/", views.department_list_api, name="department_list_api"),
    path("api/employees/", views.employee_list_api, name="employee_list_api"),

    # ========== Reports & Settings ==========
    path("reports/", views.reports, name="reports"),
    path("settings/", views.settings, name="settings"),
    
    # ========== Legacy/Deprecated URLs (redirect to new system) ==========
    path("employees/create/", views.employee_wizard_start, name="employee_create"),  # Redirect to wizard
    path("employees/setup/new/", views.employee_wizard_start, name="employee_setup_new"),
]
