"""
API URL Configuration for Core Module

Provides REST API endpoints for:
- Audit logs
- Activity logs
- System events
- Change history
- Notifications
- System health
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuditLogViewSet,
    ActivityLogViewSet,
    SystemEventViewSet,
    ChangeHistoryViewSet,
    NotificationViewSet,
    SystemHealthViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')
router.register(r'activity-logs', ActivityLogViewSet, basename='activitylog')
router.register(r'system-events', SystemEventViewSet, basename='systemevent')
router.register(r'change-history', ChangeHistoryViewSet, basename='changehistory')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'system', SystemHealthViewSet, basename='system')

app_name = 'core-api'

urlpatterns = [
    path('', include(router.urls)),
]
