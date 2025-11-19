"""
HR Assets Management System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'hr_assets'

urlpatterns = [
    # Dashboard
    path('', views.asset_dashboard, name='asset_dashboard'),

    # Vehicles
    path('vehicles/', views.vehicle_list, name='vehicle_list'),

    # Parking
    path('parking/', views.parking_dashboard, name='parking_dashboard'),

    # SIM Cards & Phones
    path('sim-cards/', views.sim_list, name='sim_list'),
    path('phones/', views.phone_list, name='phone_list'),

    # Security Cameras
    path('cameras/', views.camera_list, name='camera_list'),
]
