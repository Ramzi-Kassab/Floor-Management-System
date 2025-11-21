"""
Quality Management - URL Configuration
"""
from django.urls import path
from . import views

app_name = 'quality'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # NCR Management
    path('ncrs/', views.ncr_list, name='ncr_list'),
    path('ncrs/create/', views.ncr_create, name='ncr_create'),
    path('ncrs/<int:pk>/', views.ncr_detail, name='ncr_detail'),
    path('ncrs/<int:pk>/edit/', views.ncr_edit, name='ncr_edit'),
    path('ncrs/<int:pk>/add-analysis/', views.ncr_add_analysis, name='ncr_add_analysis'),
    path('ncrs/<int:pk>/add-action/', views.ncr_add_action, name='ncr_add_action'),
    path('ncrs/<int:pk>/close/', views.ncr_close, name='ncr_close'),

    # Calibration Management
    path('calibration/', views.calibration_list, name='calibration_list'),
    path('calibration/equipment/', views.equipment_list, name='equipment_list'),
    path('calibration/equipment/create/', views.equipment_create, name='equipment_create'),
    path('calibration/equipment/<int:pk>/', views.equipment_detail, name='equipment_detail'),
    path('calibration/equipment/<int:pk>/edit/', views.equipment_edit, name='equipment_edit'),
    path('calibration/equipment/<int:pk>/record/', views.record_calibration, name='record_calibration'),
    path('calibration/due/', views.calibration_due, name='calibration_due'),
    path('calibration/overdue/', views.calibration_overdue, name='calibration_overdue'),

    # Quality Disposition
    path('dispositions/', views.disposition_list, name='disposition_list'),
    path('dispositions/create/', views.disposition_create, name='disposition_create'),
    path('dispositions/<int:pk>/', views.disposition_detail, name='disposition_detail'),
    path('dispositions/<int:pk>/release/', views.disposition_release, name='disposition_release'),
    path('dispositions/<int:pk>/generate-coc/', views.generate_coc, name='generate_coc'),

    # Acceptance Criteria Templates
    path('criteria/', views.criteria_list, name='criteria_list'),
    path('criteria/<int:pk>/', views.criteria_detail, name='criteria_detail'),

    # Reports
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/ncr-summary/', views.ncr_summary_report, name='ncr_summary_report'),
    path('reports/calibration-status/', views.calibration_status_report, name='calibration_status_report'),

    # Settings
    path('settings/', views.settings_dashboard, name='settings'),
]
