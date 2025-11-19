"""Vendor Portal URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, RFQViewSet, QuotationViewSet, PurchaseOrderViewSet

router = DefaultRouter()
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'rfqs', RFQViewSet, basename='rfq')
router.register(r'quotations', QuotationViewSet, basename='quotation')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')

urlpatterns = [path('', include(router.urls))]
