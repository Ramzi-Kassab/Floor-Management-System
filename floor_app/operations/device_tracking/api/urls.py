"""
Device Tracking API URLs

REST API URL configuration for device tracking system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeDeviceViewSet,
    EmployeeActivityViewSet,
    EmployeePresenceViewSet,
    DeviceSessionViewSet
)

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'devices', EmployeeDeviceViewSet, basename='employee-device')
router.register(r'activities', EmployeeActivityViewSet, basename='employee-activity')
router.register(r'presence', EmployeePresenceViewSet, basename='employee-presence')
router.register(r'sessions', DeviceSessionViewSet, basename='device-session')

urlpatterns = [
    path('', include(router.urls)),
]
