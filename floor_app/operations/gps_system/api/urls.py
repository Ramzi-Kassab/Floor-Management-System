"""
GPS Verification System API URLs

REST API URL configuration for GPS verification system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LocationVerificationViewSet,
    GeofenceViewSet,
    GPSLogViewSet,
    GPSUtilsViewSet
)

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'location-verifications', LocationVerificationViewSet, basename='location-verification')
router.register(r'geofences', GeofenceViewSet, basename='geofence')
router.register(r'logs', GPSLogViewSet, basename='gps-log')
router.register(r'utils', GPSUtilsViewSet, basename='gps-utils')

urlpatterns = [
    path('', include(router.urls)),
]
