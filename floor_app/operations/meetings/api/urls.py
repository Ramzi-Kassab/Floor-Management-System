"""Meeting API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeetingRoomViewSet, RoomBookingViewSet, MorningMeetingGroupViewSet, MorningMeetingViewSet

router = DefaultRouter()
router.register(r'rooms', MeetingRoomViewSet, basename='meeting-room')
router.register(r'bookings', RoomBookingViewSet, basename='room-booking')
router.register(r'morning-groups', MorningMeetingGroupViewSet, basename='morning-group')
router.register(r'morning-meetings', MorningMeetingViewSet, basename='morning-meeting')

urlpatterns = [
    path('', include(router.urls)),
]
