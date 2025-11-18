"""
Approval Workflow API URLs

REST API URL configuration for approval workflow system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ApprovalWorkflowViewSet,
    ApprovalRequestViewSet,
    ApprovalDelegationViewSet
)

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'workflows', ApprovalWorkflowViewSet, basename='approval-workflow')
router.register(r'requests', ApprovalRequestViewSet, basename='approval-request')
router.register(r'delegations', ApprovalDelegationViewSet, basename='approval-delegation')

urlpatterns = [
    path('', include(router.urls)),
]
