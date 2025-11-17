"""
URL routing for Maintenance module.
"""
from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Assets
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/create/', views.asset_create, name='asset_create'),
    path('assets/<str:asset_code>/', views.asset_detail, name='asset_detail'),
    path('assets/<str:asset_code>/edit/', views.asset_edit, name='asset_edit'),

    # QR Code Handler
    path('qr/<str:qr_token>/', views.asset_qr, name='asset_qr'),

    # Maintenance Requests
    path('requests/', views.request_list, name='request_list'),
    path('requests/create/', views.request_create, name='request_create'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/<int:pk>/review/', views.request_review, name='request_review'),
    path('requests/<int:pk>/convert/', views.request_convert_to_wo, name='request_convert_to_wo'),

    # Work Orders
    path('workorders/', views.workorder_list, name='workorder_list'),
    path('workorders/create/', views.workorder_create, name='workorder_create'),
    path('workorders/<str:wo_number>/', views.workorder_detail, name='workorder_detail'),
    path('workorders/<str:wo_number>/edit/', views.workorder_edit, name='workorder_edit'),
    path('workorders/<str:wo_number>/assign/', views.workorder_assign, name='workorder_assign'),
    path('workorders/<str:wo_number>/complete/', views.workorder_complete, name='workorder_complete'),
    path('workorders/<str:wo_number>/add-note/', views.workorder_add_note, name='workorder_add_note'),
    path('workorders/<str:wo_number>/add-part/', views.workorder_add_part, name='workorder_add_part'),

    # Preventive Maintenance
    path('pm/', views.pm_calendar, name='pm_calendar'),
    path('pm/templates/', views.pm_template_list, name='pm_template_list'),
    path('pm/tasks/', views.pm_task_list, name='pm_task_list'),
    path('pm/tasks/<int:pk>/', views.pm_task_detail, name='pm_task_detail'),
    path('pm/tasks/<int:pk>/complete/', views.pm_task_complete, name='pm_task_complete'),

    # Downtime & Impact
    path('downtime/', views.downtime_list, name='downtime_list'),
    path('downtime/create/', views.downtime_create, name='downtime_create'),
    path('downtime/<int:pk>/', views.downtime_detail, name='downtime_detail'),
    path('downtime/<int:pk>/add-impact/', views.production_impact_create, name='production_impact_create'),
    path('downtime/impact/', views.downtime_impact, name='downtime_impact'),

    # Reports
    path('reports/', views.reports_dashboard, name='reports_dashboard'),

    # API Endpoints
    path('api/assets/search/', views.api_asset_search, name='api_asset_search'),
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
]
