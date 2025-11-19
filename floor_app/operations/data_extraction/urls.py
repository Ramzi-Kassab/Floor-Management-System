"""
Data Extraction System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'data_extraction'

urlpatterns = [
    # Extraction Workflow
    path('upload/', views.upload, name='upload'),
    path('<int:pk>/mapping/', views.field_mapping, name='field_mapping'),
    path('<int:pk>/results/', views.extraction_results, name='extraction_results'),

    # History
    path('history/', views.extraction_history, name='extraction_history'),
]
