"""
QR Code System API Serializers

Serializers for QR code system REST API.
"""

from rest_framework import serializers
from floor_app.operations.qr_system.models import (
    QRCode,
    QRScanLog,
    QRBatch,
    QRCodePrintJob,
    QRCodeTemplate
)


class QRCodeSerializer(serializers.ModelSerializer):
    """Serializer for QR codes."""

    qr_type_display = serializers.CharField(
        source='get_qr_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    related_object_repr = serializers.SerializerMethodField()
    qr_image_url = serializers.SerializerMethodField()

    class Meta:
        model = QRCode
        fields = [
            'id',
            'code',
            'qr_type',
            'qr_type_display',
            'title',
            'description',
            'related_object_repr',
            'qr_image',
            'qr_image_url',
            'status',
            'status_display',
            'scan_count',
            'first_scanned_at',
            'last_scanned_at',
            'expires_at',
            'metadata',
            'created_at',
        ]
        read_only_fields = [
            'code',
            'scan_count',
            'first_scanned_at',
            'last_scanned_at',
            'created_at',
        ]

    def get_related_object_repr(self, obj):
        """Get string representation of related object."""
        if obj.related_object:
            return str(obj.related_object)
        return None

    def get_qr_image_url(self, obj):
        """Get QR code image URL."""
        if obj.qr_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_image.url)
            return obj.qr_image.url
        return None


class QRCodeCreateSerializer(serializers.Serializer):
    """Serializer for creating QR codes via API."""

    qr_type = serializers.ChoiceField(
        choices=[
            'CUTTER', 'BIT', 'LOCATION', 'EMPLOYEE', 'JOB_CARD',
            'DELIVERY', 'ASSET', 'INVENTORY', 'DOCUMENT', 'CUSTOM'
        ]
    )
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    content_type_id = serializers.IntegerField(
        required=False,
        help_text="Content type ID for related object"
    )
    object_id = serializers.IntegerField(
        required=False,
        help_text="ID of related object"
    )
    size = serializers.IntegerField(default=300, min_value=100, max_value=1000)
    expires_at = serializers.DateTimeField(required=False)
    metadata = serializers.JSONField(required=False)


class QRScanLogSerializer(serializers.ModelSerializer):
    """Serializer for QR scan logs."""

    scanned_by_name = serializers.SerializerMethodField()
    scan_context_display = serializers.CharField(
        source='get_scan_context_display',
        read_only=True
    )
    qr_code_info = serializers.SerializerMethodField()
    location_address = serializers.SerializerMethodField()

    class Meta:
        model = QRScanLog
        fields = [
            'id',
            'qr_code',
            'qr_code_info',
            'scanned_by_user',
            'scanned_by_employee',
            'scanned_by_name',
            'scanned_at',
            'scan_context',
            'scan_context_display',
            'latitude',
            'longitude',
            'location_address',
            'device_info',
            'metadata',
        ]
        read_only_fields = ['scanned_at']

    def get_scanned_by_name(self, obj):
        """Get scanner's name."""
        if obj.scanned_by_employee:
            return obj.scanned_by_employee.full_name
        elif obj.scanned_by_user:
            return obj.scanned_by_user.get_full_name() or obj.scanned_by_user.username
        return 'Unknown'

    def get_qr_code_info(self, obj):
        """Get basic QR code information."""
        return {
            'code': obj.qr_code.code,
            'title': obj.qr_code.title,
            'type': obj.qr_code.qr_type,
        }

    def get_location_address(self, obj):
        """Get reverse-geocoded address if coordinates available."""
        if obj.latitude and obj.longitude:
            # In production, you would reverse geocode here
            return f"{obj.latitude}, {obj.longitude}"
        return None


class QRScanSerializer(serializers.Serializer):
    """Serializer for scanning QR codes via API."""

    code = serializers.CharField(max_length=200)
    scan_context = serializers.ChoiceField(
        choices=[
            'RECEIVING', 'PRODUCTION', 'QC', 'NDT', 'SHIPPING',
            'INVENTORY', 'ASSEMBLY', 'REWORK', 'STORAGE', 'DELIVERY',
            'VERIFICATION', 'TRACKING', 'INFO'
        ],
        default='INFO'
    )
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    device_info = serializers.JSONField(required=False)
    metadata = serializers.JSONField(required=False)


class QRBatchSerializer(serializers.ModelSerializer):
    """Serializer for QR batch generations."""

    qr_type_display = serializers.CharField(
        source='get_qr_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = QRBatch
        fields = [
            'id',
            'batch_name',
            'qr_type',
            'qr_type_display',
            'quantity',
            'prefix',
            'starting_number',
            'size',
            'status',
            'status_display',
            'created_by',
            'created_by_name',
            'completed_at',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['status', 'completed_at', 'created_at']

    def get_created_by_name(self, obj):
        """Get creator's name."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'System'


class QRBatchCreateSerializer(serializers.Serializer):
    """Serializer for creating batch QR codes."""

    batch_name = serializers.CharField(max_length=200)
    qr_type = serializers.ChoiceField(
        choices=[
            'CUTTER', 'BIT', 'LOCATION', 'EMPLOYEE', 'JOB_CARD',
            'DELIVERY', 'ASSET', 'INVENTORY', 'DOCUMENT', 'CUSTOM'
        ]
    )
    quantity = serializers.IntegerField(min_value=1, max_value=10000)
    prefix = serializers.CharField(max_length=20, required=False, default='QR')
    starting_number = serializers.IntegerField(min_value=1, default=1)
    size = serializers.IntegerField(default=300, min_value=100, max_value=1000)
    metadata = serializers.JSONField(required=False)


class QRCodePrintJobSerializer(serializers.ModelSerializer):
    """Serializer for QR print jobs."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    printed_by_name = serializers.SerializerMethodField()
    qr_codes_count = serializers.IntegerField(
        source='qr_codes.count',
        read_only=True
    )

    class Meta:
        model = QRCodePrintJob
        fields = [
            'id',
            'job_name',
            'template',
            'qr_codes_count',
            'paper_size',
            'layout',
            'columns',
            'rows',
            'include_text',
            'status',
            'status_display',
            'printed_by',
            'printed_by_name',
            'printed_at',
            'printer_name',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['status', 'printed_at', 'created_at']

    def get_printed_by_name(self, obj):
        """Get printer's name."""
        if obj.printed_by:
            return obj.printed_by.get_full_name() or obj.printed_by.username
        return None


class QRTemplateSerializer(serializers.ModelSerializer):
    """Serializer for QR templates."""

    class Meta:
        model = QRCodeTemplate
        fields = [
            'id',
            'name',
            'description',
            'template_type',
            'paper_size',
            'orientation',
            'columns',
            'rows',
            'qr_size',
            'include_title',
            'include_description',
            'include_code',
            'custom_css',
            'is_default',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
