"""
FIVES (5S) Audit System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'fives'

urlpatterns = [
    # Audits
    path('', views.audit_list, name='audit_list'),
    path('audit/new/', views.audit_form, name='audit_form'),
    path('audit/<int:pk>/', views.audit_detail, name='audit_detail'),
    path('audit/<int:pk>/edit/', views.audit_form, name='audit_edit'),

    # Leaderboard & Achievements
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('achievements/', views.achievements, name='achievements'),
]
