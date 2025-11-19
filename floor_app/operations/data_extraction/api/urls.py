"""Data Extraction API URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DataExtractionViewSet, DataExtractionTemplateViewSet,
    ExtractedFieldViewSet, FieldMappingViewSet
)

router = DefaultRouter()
router.register(r'extractions', DataExtractionViewSet, basename='extraction')
router.register(r'templates', DataExtractionTemplateViewSet, basename='extraction-template')
router.register(r'fields', ExtractedFieldViewSet, basename='extracted-field')
router.register(r'mappings', FieldMappingViewSet, basename='field-mapping')

urlpatterns = [
    path('', include(router.urls)),
]
