"""
Cutter BOM & Map Grid System API URLs

REST API URL configuration for Cutter BOM and Map grid system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CutterBOMGridViewSet,
    CutterBOMGridValidationViewSet,
    CutterMapGridViewSet,
    CutterMapGridValidationViewSet
)

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'bom-grids', CutterBOMGridViewSet, basename='cutter-bom-grid')
router.register(r'bom-grid-validations', CutterBOMGridValidationViewSet, basename='cutter-bom-grid-validation')
router.register(r'map-grids', CutterMapGridViewSet, basename='cutter-map-grid')
router.register(r'map-grid-validations', CutterMapGridValidationViewSet, basename='cutter-map-grid-validation')

urlpatterns = [
    path('', include(router.urls)),
]
