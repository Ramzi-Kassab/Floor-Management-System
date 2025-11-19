"""
User Preferences System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'user_preferences'

urlpatterns = [
    # Preferences
    path('', views.preferences_dashboard, name='preferences_dashboard'),
    path('notifications/', views.notification_settings, name='notification_settings'),
]
