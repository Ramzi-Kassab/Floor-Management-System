"""Chat API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, ChatMessageViewSet, ChatNotificationViewSet

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chat-room')
router.register(r'messages', ChatMessageViewSet, basename='chat-message')
router.register(r'notifications', ChatNotificationViewSet, basename='chat-notification')

urlpatterns = [
    path('', include(router.urls)),
]
