"""
Meeting Management System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    # Meetings
    path('', views.meeting_list, name='meeting_list'),
    path('schedule/', views.meeting_scheduler, name='meeting_scheduler'),

    # Room Booking
    path('rooms/', views.room_booking, name='room_booking'),
]
