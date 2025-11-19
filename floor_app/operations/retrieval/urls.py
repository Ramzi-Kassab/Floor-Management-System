"""
Retrieval System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'retrieval'

urlpatterns = [
    # Employee views
    path('', views.retrieval_dashboard, name='dashboard'),
    path('create/<int:content_type_id>/<int:object_id>/', views.create_retrieval_request, name='create_request'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('request/<int:pk>/complete/', views.complete_retrieval, name='complete_retrieval'),
    path('request/<int:pk>/cancel/', views.cancel_retrieval, name='cancel_retrieval'),

    # Supervisor views
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/<int:pk>/', views.approve_retrieval, name='approve_retrieval'),
    path('supervisor/<int:pk>/reject/', views.reject_retrieval, name='reject_retrieval'),

    # Metrics
    path('metrics/', views.employee_metrics, name='my_metrics'),
    path('metrics/<int:employee_id>/', views.employee_metrics, name='employee_metrics'),
]
