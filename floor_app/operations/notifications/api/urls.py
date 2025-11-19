"""
Notification API URLs

REST API URL configuration for notification system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationChannelViewSet,
    NotificationTemplateViewSet,
    NotificationViewSet,
    UserNotificationPreferenceViewSet,
    AnnouncementViewSet
)

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'channels', NotificationChannelViewSet, basename='notification-channel')
router.register(r'templates', NotificationTemplateViewSet, basename='notification-template')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'preferences', UserNotificationPreferenceViewSet, basename='notification-preference')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('', include(router.urls)),
]
