"""Vendor Portal Serializers"""
from rest_framework import serializers
from floor_app.operations.vendor_portal.models import Vendor, RFQ, Quotation, PurchaseOrder

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'

class RFQSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    class Meta:
        model = RFQ
        fields = '__all__'

class RFQCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    issue_date = serializers.DateField()
    submission_deadline = serializers.DateTimeField()
    required_delivery_date = serializers.DateField(required=False, allow_null=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    project = serializers.CharField(max_length=100, required=False, allow_blank=True)
    priority = serializers.CharField(default='MEDIUM')
    line_items = serializers.ListField(default=list)
    vendor_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    published_publicly = serializers.BooleanField(default=False)
    payment_terms = serializers.CharField(required=False, allow_blank=True)
    delivery_terms = serializers.CharField(required=False, allow_blank=True)
    terms_and_conditions = serializers.CharField(required=False, allow_blank=True)

class QuotationSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.company_name', read_only=True)
    rfq_title = serializers.CharField(source='rfq.title', read_only=True)
    class Meta:
        model = Quotation
        fields = '__all__'

class QuotationSubmitSerializer(serializers.Serializer):
    line_items = serializers.ListField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='USD')
    payment_terms = serializers.CharField(required=False, allow_blank=True)
    delivery_timeframe = serializers.CharField(max_length=200, required=False, allow_blank=True)
    warranty = serializers.CharField(required=False, allow_blank=True)
    validity_days = serializers.IntegerField(default=30)

class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.company_name', read_only=True)
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
