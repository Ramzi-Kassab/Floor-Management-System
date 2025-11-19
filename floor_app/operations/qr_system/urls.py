"""
QR Code System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'qr_system'

urlpatterns = [
    # QR Code Management
    path('generate/', views.generate, name='generate'),
    path('', views.qr_list, name='qr_list'),
    path('<int:pk>/', views.qr_detail, name='qr_detail'),

    # Scans & Integration
    path('scans/', views.scan_history, name='scan_history'),
    path('integration/', views.integration_guide, name='integration_guide'),
]
