from django.urls import path

from . import views_employee_setup
from . import views_department

# 🔹 This line defines the namespace for this urls file
app_name = "hr"

urlpatterns = [
    # Create new employee
    path(
        "employees/create/",
        views_employee_setup.employee_create,
        name="employee_create",
    ),

    # Edit existing employee
    path(
        "employees/<int:pk>/edit/",
        views_employee_setup.employee_edit,
        name="employee_edit",
    ),

    # DEPRECATED: Backward compatibility redirects
    # (these redirect to the new views)
    path(
        "employees/setup/new/",
        views_employee_setup.employee_setup,
        name="employee_setup_new",
    ),

    path(
        "employees/setup/<int:employee_id>/",
        views_employee_setup.employee_setup,
        name="employee_setup",
    ),

    path(
        "employees/setup/",
        views_employee_setup.employee_setup_list,
        name="employee_setup_list",
    ),

    # AJAX Save Endpoints for Progressive Tab Saves
    path(
        "employees/ajax/save-person/",
        views_employee_setup.save_person_tab,
        name="save_person_tab",
    ),
    path(
        "employees/ajax/save-employee/",
        views_employee_setup.save_employee_tab,
        name="save_employee_tab",
    ),
    path(
        "employees/ajax/save-phones/",
        views_employee_setup.save_phones_tab,
        name="save_phones_tab",
    ),
    path(
        "employees/ajax/save-emails/",
        views_employee_setup.save_emails_tab,
        name="save_emails_tab",
    ),
    path(
        "employees/ajax/save-addresses/",
        views_employee_setup.save_addresses_tab,
        name="save_addresses_tab",
    ),

    # Person Lookup and Management APIs
    path(
        "persons/api/list/",
        views_employee_setup.person_list_api,
        name="person_list_api",
    ),
    path(
        "persons/api/<int:person_id>/",
        views_employee_setup.person_detail_api,
        name="person_detail_api",
    ),

    # Phones List API
    path(
        "phones/api/list/",
        views_employee_setup.phones_list_api,
        name="phones_list_api",
    ),

    # ========== DEPARTMENTS ==========
    # List all departments
    path(
        "departments/",
        views_department.DepartmentListView.as_view(),
        name="department_list",
    ),

    # Create new department
    path(
        "departments/create/",
        views_department.DepartmentCreateView.as_view(),
        name="department_create",
    ),

    # View department details
    path(
        "departments/<int:pk>/",
        views_department.DepartmentDetailView.as_view(),
        name="department_detail",
    ),

    # Edit department
    path(
        "departments/<int:pk>/edit/",
        views_department.DepartmentUpdateView.as_view(),
        name="department_update",
    ),

    # Delete department
    path(
        "departments/<int:pk>/delete/",
        views_department.DepartmentDeleteView.as_view(),
        name="department_delete",
    ),
]
