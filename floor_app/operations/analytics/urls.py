"""
URL Configuration for Analytics Module
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Main dashboard
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),

    # Activity tracking
    path('activities/', views.UserActivityListView.as_view(), name='activity_list'),

    # Sessions
    path('sessions/', views.UserSessionListView.as_view(), name='session_list'),
    path('sessions/<int:pk>/', views.UserSessionDetailView.as_view(), name='session_detail'),

    # Errors
    path('errors/', views.ErrorLogListView.as_view(), name='error_list'),
    path('errors/<int:pk>/', views.ErrorLogDetailView.as_view(), name='error_detail'),

    # Module usage
    path('modules/', views.ModuleUsageView.as_view(), name='module_usage'),

    # User reports
    path('users/<int:pk>/report/', views.UserReportView.as_view(), name='user_report'),

    # API endpoints
    path('api/realtime-stats/', views.api_realtime_stats, name='api_realtime_stats'),
    path('api/module-stats/', views.api_module_stats, name='api_module_stats'),
    path('api/user-activity/<int:user_id>/', views.api_user_activity_timeline, name='api_user_activity'),

    # Export
    path('export/', views.export_analytics_report, name='export_report'),
]
