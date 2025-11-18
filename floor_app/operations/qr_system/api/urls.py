"""
QR Code System API URLs

REST API URL configuration for QR code system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QRCodeViewSet,
    QRBatchGenerationViewSet,
    QRScanLogViewSet,
    QRPrintJobViewSet,
    QRTemplateViewSet
)

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'codes', QRCodeViewSet, basename='qr-code')
router.register(r'batches', QRBatchGenerationViewSet, basename='qr-batch')
router.register(r'scans', QRScanLogViewSet, basename='qr-scan')
router.register(r'print-jobs', QRPrintJobViewSet, basename='qr-print-job')
router.register(r'templates', QRTemplateViewSet, basename='qr-template')

urlpatterns = [
    path('', include(router.urls)),
]
