"""
Utility Tools API URLs

REST API URL configuration for utility tools.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ImageToolsViewSet,
    FileConversionViewSet,
    TextToolsViewSet,
    CalculatorToolsViewSet
)

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'images', ImageToolsViewSet, basename='image-tools')
router.register(r'file-conversion', FileConversionViewSet, basename='file-conversion')
router.register(r'text', TextToolsViewSet, basename='text-tools')
router.register(r'calculator', CalculatorToolsViewSet, basename='calculator-tools')

urlpatterns = [
    path('', include(router.urls)),
]
