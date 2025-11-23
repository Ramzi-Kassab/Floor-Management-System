"""
REST API URLs for HR Module
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PersonViewSet, DepartmentViewSet, PositionViewSet,
    EmployeeViewSet, ContractViewSet,
    ShiftViewSet, ShiftAssignmentViewSet,
    AssetViewSet, AssetAssignmentViewSet,
    LeaveTypeViewSet, LeaveRequestViewSet
)

app_name = 'hr_api'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'persons', PersonViewSet, basename='person')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'shifts', ShiftViewSet, basename='shift')
router.register(r'shift-assignments', ShiftAssignmentViewSet, basename='shift-assignment')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'asset-assignments', AssetAssignmentViewSet, basename='asset-assignment')
router.register(r'leave-types', LeaveTypeViewSet, basename='leave-type')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')

urlpatterns = [
    path('', include(router.urls)),
]
