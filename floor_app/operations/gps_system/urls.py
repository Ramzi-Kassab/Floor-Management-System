"""
GPS Location Verification System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'gps_system'

urlpatterns = [
    # Verification
    path('', views.verification_dashboard, name='verification_dashboard'),
    path('verify/', views.verification_request, name='verification_request'),
    path('history/', views.verification_history, name='verification_history'),
    path('map/<int:verification_id>/', views.map_view, name='map_view'),

    # Geofence Zones
    path('zones/', views.zone_list, name='zone_list'),
    path('zones/new/', views.zone_form, name='zone_form'),
    path('zones/<int:pk>/edit/', views.zone_form, name='zone_edit'),
]
