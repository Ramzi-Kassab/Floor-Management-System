from django.urls import path

from . import views_employee_setup

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
]
