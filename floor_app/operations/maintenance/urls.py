"""
URL configuration for Maintenance & Asset Management module.
"""
from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('api/stats/', views.api_dashboard_stats, name='api_stats'),

    # Assets
    path('assets/', views.AssetListView.as_view(), name='asset_list'),
    path('assets/create/', views.AssetCreateView.as_view(), name='asset_create'),
    path('assets/<int:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('assets/<int:pk>/edit/', views.AssetUpdateView.as_view(), name='asset_edit'),
    path('assets/<int:pk>/qr/', views.asset_qr_generate, name='asset_qr'),
    path('assets/scan/<str:token>/', views.asset_scan, name='asset_scan'),

    # Maintenance Requests
    path('requests/', views.MaintenanceRequestListView.as_view(), name='request_list'),
    path('requests/create/', views.MaintenanceRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/approve/', views.request_approve, name='request_approve'),
    path('requests/<int:pk>/reject/', views.request_reject, name='request_reject'),
    path('requests/<int:pk>/convert/', views.request_convert_to_wo, name='request_convert'),

    # Work Orders
    path('work-orders/', views.WorkOrderListView.as_view(), name='work_order_list'),
    path('work-orders/create/', views.WorkOrderCreateView.as_view(), name='work_order_create'),
    path('work-orders/<int:pk>/', views.WorkOrderDetailView.as_view(), name='work_order_detail'),
    path('work-orders/<int:pk>/start/', views.work_order_start, name='work_order_start'),
    path('work-orders/<int:pk>/complete/', views.work_order_complete, name='work_order_complete'),

    # Preventive Maintenance
    path('pm/plans/', views.PMPlanListView.as_view(), name='pm_plan_list'),
    path('pm/calendar/', views.pm_calendar, name='pm_calendar'),
    path('pm/tasks/', views.PMTaskListView.as_view(), name='pm_task_list'),
    path('pm/tasks/<int:pk>/start/', views.pm_task_start, name='pm_task_start'),
    path('pm/tasks/<int:pk>/complete/', views.pm_task_complete, name='pm_task_complete'),

    # Downtime
    path('downtime/', views.DowntimeListView.as_view(), name='downtime_list'),
    path('downtime/create/', views.DowntimeCreateView.as_view(), name='downtime_create'),
    path('downtime/<int:pk>/end/', views.downtime_end, name='downtime_end'),
    path('downtime/lost-sales/', views.lost_sales_list, name='lost_sales_list'),

    # Settings
    path('settings/', views.settings_dashboard, name='settings'),
    path('settings/categories/', views.CategoryListView.as_view(), name='category_list'),
    path('settings/locations/', views.LocationListView.as_view(), name='location_list'),
]
