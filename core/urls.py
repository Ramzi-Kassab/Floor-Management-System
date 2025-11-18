"""
Core app URLs.

Includes:
- Main dashboard
- User preferences
- Finance/ERP integration
- Cost center management
- Loss of sale tracking
- Django core tables front-end
- API endpoints
"""

from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Main Dashboard
    path("", views.main_dashboard, name="home"),

    # User Preferences
    path("settings/", views.user_preferences, name="user_preferences"),
    path("settings/reset-columns/", views.reset_table_columns, name="reset_table_columns"),

    # API Endpoints
    path("api/user-preferences/table-columns/", views.TableColumnsAPIView.as_view(), name="api_table_columns"),

    # Finance Dashboard
    path("finance/", views.finance_dashboard, name="finance_dashboard"),

    # Cost Centers
    path("cost-centers/", views.CostCenterListView.as_view(), name="costcenter_list"),
    path("cost-centers/create/", views.CostCenterCreateView.as_view(), name="costcenter_create"),
    path("cost-centers/<int:pk>/", views.CostCenterDetailView.as_view(), name="costcenter_detail"),
    path("cost-centers/<int:pk>/edit/", views.CostCenterUpdateView.as_view(), name="costcenter_edit"),

    # ERP References
    path("erp-references/", views.ERPReferenceListView.as_view(), name="erpreference_list"),

    # Loss of Sale Events
    path("loss-of-sale/", views.LossOfSaleEventListView.as_view(), name="lossofsale_list"),
    path("loss-of-sale/create/", views.LossOfSaleEventCreateView.as_view(), name="lossofsale_create"),
    path("loss-of-sale/<int:pk>/", views.LossOfSaleEventDetailView.as_view(), name="lossofsale_detail"),

    # Django Core Tables Front-End Views

    # User Management
    path("system/users/", views.UserListView.as_view(), name="user_list"),
    path("system/users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("system/users/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("system/users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_edit"),
    path("system/users/<int:pk>/password/", views.user_password_change, name="user_password_change"),
    path("system/users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("system/users/<int:pk>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),
    path("system/users/<int:pk>/permissions/", views.user_permissions, name="user_permissions"),

    # Group Management
    path("system/groups/", views.GroupListView.as_view(), name="group_list"),
    path("system/groups/create/", views.GroupCreateView.as_view(), name="group_create"),
    path("system/groups/<int:pk>/", views.GroupDetailView.as_view(), name="group_detail"),
    path("system/groups/<int:pk>/edit/", views.GroupUpdateView.as_view(), name="group_edit"),
    path("system/groups/<int:pk>/delete/", views.group_delete, name="group_delete"),

    # Permissions (read-only)
    path("system/permissions/", views.PermissionListView.as_view(), name="permission_list"),

    # Other system views
    path("system/content-types/", views.ContentTypeListView.as_view(), name="contenttype_list"),
    path("system/admin-log/", views.AdminLogListView.as_view(), name="adminlog_list"),
    path("system/sessions/", views.SessionListView.as_view(), name="session_list"),
]
