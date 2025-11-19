"""
Approval Workflow System URL Configuration
"""

from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    # Approval Requests
    path('', views.pending_approvals, name='pending_approvals'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('request/new/', views.request_form, name='request_form'),
    path('history/', views.history, name='history'),

    # Workflows
    path('workflows/', views.workflow_list, name='workflow_list'),
    path('workflows/designer/', views.workflow_designer, name='workflow_designer'),

    # Delegations
    path('delegations/', views.delegation_manage, name='delegation_manage'),
]
