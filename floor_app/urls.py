"""
Floor App URLs - System-wide templates and features.

Includes:
- User-facing features (notifications, profile, dashboard)
- Help system (help center, FAQ, onboarding)
- Admin tools (admin dashboard, audit logs, user management)
- API management
- System pages (maintenance, contact, privacy policy)
- Universal features (search, reporting, settings)
"""

from django.urls import path
from . import views

app_name = "floor_app"

urlpatterns = [
    # ===== USER-FACING FEATURES =====

    # Notifications
    path("notifications/", views.notification_center, name="notification_center"),
    path("notifications/mark-read/<int:pk>/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/mark-all-read/", views.mark_all_notifications_read, name="mark_all_notifications_read"),
    path("notifications/settings/", views.notification_settings, name="notification_settings"),

    # User Profile
    path("profile/", views.user_profile, name="user_profile"),
    path("profile/edit/", views.user_profile_edit, name="user_profile_edit"),
    path("profile/avatar/", views.user_avatar_upload, name="user_avatar_upload"),
    path("profile/password/", views.user_password_change_view, name="user_password_change_view"),
    path("profile/preferences/", views.user_preferences_view, name="user_preferences_view"),
    path("profile/sessions/", views.user_active_sessions, name="user_active_sessions"),

    # ===== HELP SYSTEM =====

    # Help Center
    path("help/", views.help_center, name="help_center"),
    path("help/article/<slug:slug>/", views.help_article, name="help_article"),
    path("help/category/<slug:category>/", views.help_category, name="help_category"),
    path("help/search/", views.help_search, name="help_search"),

    # FAQ
    path("faq/", views.faq, name="faq"),
    path("faq/category/<slug:category>/", views.faq_category, name="faq_category"),

    # Onboarding
    path("onboarding/", views.onboarding_tutorial, name="onboarding_tutorial"),
    path("onboarding/complete/", views.onboarding_complete, name="onboarding_complete"),
    path("onboarding/skip/", views.onboarding_skip, name="onboarding_skip"),

    # Contact Support
    path("support/", views.contact_support, name="contact_support"),
    path("support/submit/", views.submit_support_ticket, name="submit_support_ticket"),
    path("support/ticket/<int:pk>/", views.support_ticket_detail, name="support_ticket_detail"),

    # ===== ADMIN & MANAGEMENT =====

    # Admin Dashboard
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/system-health/", views.system_health_api, name="system_health_api"),
    path("admin/user-activity/", views.user_activity_api, name="user_activity_api"),

    # Audit Logs
    path("audit-logs/", views.audit_logs, name="audit_logs"),
    path("audit-logs/export/", views.audit_logs_export, name="audit_logs_export"),
    path("audit-logs/detail/<int:pk>/", views.audit_log_detail, name="audit_log_detail"),

    # User Management
    path("users/", views.user_management, name="user_management"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:pk>/", views.user_detail_view, name="user_detail_view"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete_view, name="user_delete_view"),
    path("users/<int:pk>/toggle-status/", views.user_toggle_status, name="user_toggle_status"),
    path("users/<int:pk>/permissions/", views.user_permissions_edit, name="user_permissions_edit"),
    path("users/bulk-action/", views.users_bulk_action, name="users_bulk_action"),
    path("users/export/", views.users_export, name="users_export"),

    # API Management
    path("api-management/", views.api_management, name="api_management"),
    path("api-keys/create/", views.api_key_create, name="api_key_create"),
    path("api-keys/<int:pk>/regenerate/", views.api_key_regenerate, name="api_key_regenerate"),
    path("api-keys/<int:pk>/delete/", views.api_key_delete, name="api_key_delete"),
    path("api/usage-stats/", views.api_usage_stats, name="api_usage_stats"),
    path("webhooks/create/", views.webhook_create, name="webhook_create"),
    path("webhooks/<int:pk>/test/", views.webhook_test, name="webhook_test"),
    path("webhooks/<int:pk>/toggle/", views.webhook_toggle, name="webhook_toggle"),

    # ===== UNIVERSAL FEATURES =====

    # Global Search (enhanced)
    path("search/", views.global_search_view, name="global_search_view"),
    path("search/suggestions/", views.search_suggestions, name="search_suggestions"),

    # Reporting Hub
    path("reporting/", views.reporting_hub, name="reporting_hub"),
    path("reporting/generate/", views.generate_report, name="generate_report"),
    path("reporting/<int:pk>/", views.report_detail, name="report_detail"),
    path("reporting/<int:pk>/download/", views.report_download, name="report_download"),
    path("reporting/<int:pk>/schedule/", views.report_schedule, name="report_schedule"),

    # System Settings
    path("settings/system/", views.system_settings, name="system_settings"),
    path("settings/system/update/", views.system_settings_update, name="system_settings_update"),
    path("settings/modules/", views.module_settings, name="module_settings"),
    path("settings/integrations/", views.integration_settings, name="integration_settings"),

    # Dashboard Customization
    path("dashboard/customize/", views.dashboard_customization, name="dashboard_customization"),
    path("dashboard/widgets/add/", views.dashboard_widget_add, name="dashboard_widget_add"),
    path("dashboard/widgets/<int:pk>/remove/", views.dashboard_widget_remove, name="dashboard_widget_remove"),
    path("dashboard/widgets/reorder/", views.dashboard_widgets_reorder, name="dashboard_widgets_reorder"),
    path("dashboard/layout/save/", views.dashboard_layout_save, name="dashboard_layout_save"),
    path("dashboard/layout/reset/", views.dashboard_layout_reset, name="dashboard_layout_reset"),

    # ===== SYSTEM PAGES =====

    # Maintenance Mode
    path("maintenance/", views.maintenance_page, name="maintenance_page"),

    # Privacy Policy
    path("privacy/", views.privacy_policy, name="privacy_policy"),

    # Terms of Service
    path("terms/", views.terms_of_service, name="terms_of_service"),

    # ===== API ENDPOINTS (JSON responses) =====

    # Notifications API
    path("api/notifications/unread-count/", views.api_notifications_unread_count, name="api_notifications_unread_count"),
    path("api/notifications/recent/", views.api_notifications_recent, name="api_notifications_recent"),

    # User Stats API
    path("api/user/stats/", views.api_user_stats, name="api_user_stats"),
    path("api/user/activity/", views.api_user_activity, name="api_user_activity"),
    path("api/user/save-theme/", views.api_user_save_theme, name="api_user_save_theme"),

    # System Stats API (for admin dashboard)
    path("api/system/stats/", views.api_system_stats, name="api_system_stats"),
    path("api/system/alerts/", views.api_system_alerts, name="api_system_alerts"),
]
