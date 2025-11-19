"""
In-App Chat System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Chat Interface
    path('', views.chat_interface, name='chat_interface'),

    # Channels & DMs
    path('channels/', views.channel_list, name='channel_list'),
    path('direct/', views.direct_messages, name='direct_messages'),
    path('contacts/', views.user_contacts, name='user_contacts'),
]
