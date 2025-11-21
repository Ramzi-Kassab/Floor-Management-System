"""
Planning & KPI Management - URL Configuration
"""
from django.urls import path
from . import views

app_name = 'planning'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Resource Management
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/create/', views.resource_create, name='resource_create'),
    path('resources/<int:pk>/', views.resource_detail, name='resource_detail'),
    path('resources/<int:pk>/edit/', views.resource_edit, name='resource_edit'),

    # Capacity Planning
    path('capacity/', views.capacity_overview, name='capacity_overview'),
    path('capacity/<int:resource_id>/plan/', views.capacity_plan, name='capacity_plan'),
    path('capacity/bottlenecks/', views.bottleneck_analysis, name='bottleneck_analysis'),

    # Schedule Management
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/', views.schedule_detail, name='schedule_detail'),
    path('schedules/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedules/<int:pk>/publish/', views.schedule_publish, name='schedule_publish'),
    path('schedules/<int:pk>/operations/', views.schedule_operations, name='schedule_operations'),

    # Scheduled Operations
    path('operations/<int:pk>/', views.operation_detail, name='operation_detail'),
    path('operations/<int:pk>/start/', views.operation_start, name='operation_start'),
    path('operations/<int:pk>/complete/', views.operation_complete, name='operation_complete'),

    # KPI Management
    path('kpis/', views.kpi_dashboard, name='kpi_dashboard'),
    path('kpis/definitions/', views.kpi_definition_list, name='kpi_definition_list'),
    path('kpis/definitions/create/', views.kpi_definition_create, name='kpi_definition_create'),
    path('kpis/definitions/<int:pk>/', views.kpi_definition_detail, name='kpi_definition_detail'),
    path('kpis/values/', views.kpi_value_list, name='kpi_value_list'),
    path('kpis/values/record/', views.kpi_value_record, name='kpi_value_record'),
    path('kpis/trends/', views.kpi_trends, name='kpi_trends'),

    # WIP Tracking
    path('wip/', views.wip_board, name='wip_board'),
    path('wip/snapshot/', views.wip_snapshot, name='wip_snapshot'),
    path('wip/history/', views.wip_history, name='wip_history'),

    # Job Metrics
    path('metrics/', views.metrics_overview, name='metrics_overview'),
    path('metrics/job/<int:job_card_id>/', views.job_metrics_detail, name='job_metrics_detail'),

    # Delivery Forecasting
    path('forecasts/', views.forecast_list, name='forecast_list'),
    path('forecasts/at-risk/', views.at_risk_jobs, name='at_risk_jobs'),
    path('forecasts/<int:pk>/', views.forecast_detail, name='forecast_detail'),

    # Reports
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/otd/', views.otd_report, name='otd_report'),
    path('reports/utilization/', views.utilization_report, name='utilization_report'),

    # Settings
    path('settings/', views.settings_dashboard, name='settings'),
]
