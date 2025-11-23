"""
URL patterns for core system monitoring

Provides URLs for:
- System dashboard
- Activity and audit log viewers
- Export utilities
- API endpoints
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard and viewers
    path('dashboard/', views.system_dashboard, name='dashboard'),
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('system-events/', views.system_events, name='system_events'),
    path('user-activity/<str:username>/', views.user_activity_report, name='user_activity_report'),

    # Theme and preferences
    path('theme-settings/', views.theme_settings, name='theme_settings'),

    # Export endpoints
    path('export/activity-logs/', views.export_activity_logs, name='export_activity_logs'),
    path('export/audit-logs/', views.export_audit_logs, name='export_audit_logs'),

    # API endpoints (JSON)
    path('api/health/', views.api_system_health, name='api_health'),
    path('api/activity-stats/', views.api_activity_stats, name='api_activity_stats'),
    path('api/audit-stats/', views.api_audit_stats, name='api_audit_stats'),
]
