"""
Utility Tools System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'utility_tools'

urlpatterns = [
    # Tools Dashboard
    path('', views.tools_dashboard, name='tools_dashboard'),

    # Calculators
    path('calculators/', views.calculators, name='calculators'),

    # File Tools
    path('files/', views.file_tools, name='file_tools'),
]
