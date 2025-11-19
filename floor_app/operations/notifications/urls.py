"""
Notification & Announcement System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification Center
    path('', views.notification_center, name='notification_center'),
    path('<int:pk>/', views.notification_detail, name='notification_detail'),
    path('preferences/', views.user_preferences, name='user_preferences'),

    # Announcements
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/<int:pk>/', views.announcement_detail, name='announcement_detail'),

    # Admin/Staff
    path('channels/', views.channel_config, name='channel_config'),
    path('templates/', views.template_editor, name='template_editor'),
    path('delivery/', views.delivery_status, name='delivery_status'),
]
