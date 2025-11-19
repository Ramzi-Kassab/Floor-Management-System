"""
Device Tracking System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'device_tracking'

urlpatterns = [
    # Dashboard & Devices
    path('', views.dashboard, name='dashboard'),
    path('devices/', views.device_list, name='device_list'),
    path('devices/<int:pk>/', views.device_detail, name='device_detail'),
    path('devices/register/', views.device_register, name='device_register'),

    # Check-in & Location
    path('check-in/', views.check_in, name='check_in'),
    path('location/<int:device_id>/', views.location_history, name='location_history'),
]
