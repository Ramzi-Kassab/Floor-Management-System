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
