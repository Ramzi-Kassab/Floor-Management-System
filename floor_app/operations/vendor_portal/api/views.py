"""Vendor Portal Views"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from floor_app.operations.vendor_portal.models import Vendor, RFQ, Quotation, PurchaseOrder
from floor_app.operations.vendor_portal.services import VendorService
from .serializers import *

class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

class RFQViewSet(viewsets.ModelViewSet):
    serializer_class = RFQSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RFQ.objects.select_related('requested_by')

    def create(self, request):
        serializer = RFQCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rfq = VendorService.create_rfq(request.user, serializer.validated_data)
        return Response(RFQSerializer(rfq).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        rfq = VendorService.publish_rfq(int(pk))
        return Response(RFQSerializer(rfq).data)

    @action(detail=True, methods=['post'])
    def award(self, request, pk=None):
        quotation_id = request.data.get('quotation_id')
        rfq = VendorService.award_rfq(int(pk), quotation_id, request.user)
        return Response(RFQSerializer(rfq).data)

class QuotationViewSet(viewsets.ModelViewSet):
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quotation.objects.select_related('rfq', 'vendor')

    @action(detail=False, methods=['post'], url_path='submit/(?P<rfq_id>[^/.]+)')
    def submit_quotation(self, request, rfq_id=None):
        serializer = QuotationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor = request.user.vendor_profile if hasattr(request.user, 'vendor_profile') else None
        quotation = VendorService.submit_quotation(int(rfq_id), vendor, serializer.validated_data)
        return Response(QuotationSerializer(quotation).data, status=status.HTTP_201_CREATED)

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('vendor', 'quotation')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
