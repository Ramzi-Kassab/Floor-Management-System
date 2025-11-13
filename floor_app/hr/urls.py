from django.urls import path

from . import views_employee_setup

# 🔹 This line defines the namespace for this urls file
app_name = "hr"

urlpatterns = [
    # Setup wizard for new employee
    path(
        "employees/setup/new/",
        views_employee_setup.employee_setup,
        name="employee_setup_new",
    ),

    # Setup wizard for existing employee
    path(
        "employees/setup/<int:employee_id>/",
        views_employee_setup.employee_setup,
        name="employee_setup",
    ),

    # 🔹 "List" / entry point used by the navbar: hr:employee_setup_list
    # For now, we just redirect to the "new" page (you can later change
    # this to a proper list if you want).
    path(
        "employees/setup/",
        views_employee_setup.employee_setup_list,
        name="employee_setup_list",
    ),
]
