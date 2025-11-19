"""
Health and Observation Card (HOC) System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'hoc'

urlpatterns = [
    # Observations
    path('', views.observation_list, name='observation_list'),
    path('submit/', views.submit_hoc, name='submit_hoc'),
    path('observation/<int:pk>/', views.observation_detail, name='observation_detail'),

    # Analytics
    path('analytics/', views.hoc_analytics, name='hoc_analytics'),
]
