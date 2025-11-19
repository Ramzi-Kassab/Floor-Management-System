"""
Journey Management System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'journey_management'

urlpatterns = [
    # Journey Management
    path('', views.journey_list, name='journey_list'),
    path('plan/', views.journey_planner, name='journey_planner'),
    path('<int:pk>/tracking/', views.journey_tracking, name='journey_tracking'),
]
