from django.urls import path
from . import views

app_name = 'qrcodes'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Central scan endpoint
    path('scan/<uuid:token>/', views.scan_handler, name='scan'),

    # QR Code image generation
    path('img/<uuid:token>.<str:format>/', views.qr_image, name='image'),
    path('img/label/<uuid:token>/', views.qr_label_image, name='label_image'),

    # QCode management
    path('codes/', views.QCodeListView.as_view(), name='list'),
    path('codes/<uuid:token>/', views.QCodeDetailView.as_view(), name='detail'),
    path('codes/generate/', views.generate_qcode, name='generate'),
    path('codes/<uuid:token>/deactivate/', views.deactivate_qcode, name='deactivate'),
    path('codes/<uuid:token>/reactivate/', views.reactivate_qcode, name='reactivate'),
    path('codes/<uuid:token>/regenerate/', views.regenerate_token, name='regenerate'),

    # Scan logs
    path('logs/', views.ScanLogListView.as_view(), name='scan_logs'),
    path('logs/export/', views.export_scan_logs, name='export_logs'),

    # Equipment
    path('equipment/', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/create/', views.EquipmentCreateView.as_view(), name='equipment_create'),
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment_detail'),
    path('equipment/<int:pk>/edit/', views.EquipmentUpdateView.as_view(), name='equipment_edit'),
    path('equipment/<int:pk>/report/', views.create_maintenance_request, name='equipment_report'),
    path('equipment/<int:pk>/generate-qr/', views.generate_equipment_qr, name='equipment_generate_qr'),

    # Maintenance
    path('maintenance/', views.MaintenanceListView.as_view(), name='maintenance_list'),
    path('maintenance/<int:pk>/', views.MaintenanceDetailView.as_view(), name='maintenance_detail'),
    path('maintenance/<int:pk>/complete/', views.complete_maintenance, name='maintenance_complete'),

    # Containers
    path('containers/', views.ContainerListView.as_view(), name='container_list'),
    path('containers/create/', views.ContainerCreateView.as_view(), name='container_create'),
    path('containers/<int:pk>/', views.ContainerDetailView.as_view(), name='container_detail'),
    path('containers/<int:pk>/edit/', views.ContainerUpdateView.as_view(), name='container_edit'),
    path('containers/<int:pk>/generate-qr/', views.generate_container_qr, name='container_generate_qr'),

    # Process execution
    path('process/start/<int:route_step_id>/', views.start_process, name='process_start'),
    path('process/action/<int:execution_id>/', views.process_action, name='process_action'),

    # BOM Material pickup
    path('bom/<int:bom_line_id>/', views.bom_material_view, name='bom_material'),
    path('bom/pickup/<int:bom_line_id>/', views.bom_pickup, name='bom_pickup'),
    path('bom/return/<int:bom_line_id>/', views.bom_return, name='bom_return'),

    # Movement logs
    path('movements/', views.MovementLogListView.as_view(), name='movement_list'),

    # Bulk operations
    path('bulk/generate/', views.bulk_generate, name='bulk_generate'),
    path('bulk/print/', views.bulk_print, name='bulk_print'),

    # API endpoints
    path('api/scan/', views.api_scan, name='api_scan'),
    path('api/qcode/<uuid:token>/', views.api_qcode_info, name='api_qcode_info'),
]
