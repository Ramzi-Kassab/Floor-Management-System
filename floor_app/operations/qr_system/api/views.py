"""
QR Code System API Views

REST API viewsets for QR code system.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from django.http import HttpResponse

from floor_app.operations.qr_system.models import (
    QRCode,
    QRScanLog,
    QRBatchGeneration,
    QRPrintJob,
    QRTemplate
)
from floor_app.operations.qr_system.services import QRCodeService
from .serializers import (
    QRCodeSerializer,
    QRCodeCreateSerializer,
    QRScanLogSerializer,
    QRScanSerializer,
    QRBatchGenerationSerializer,
    QRBatchGenerationCreateSerializer,
    QRPrintJobSerializer,
    QRTemplateSerializer
)


class QRCodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing QR codes.

    list: Get all QR codes
    retrieve: Get a specific QR code
    create: Generate a new QR code
    update: Update QR code details
    destroy: Deactivate a QR code
    """

    queryset = QRCode.objects.filter(status='ACTIVE').select_related('content_type')
    serializer_class = QRCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['qr_type', 'status']
    search_fields = ['code', 'title', 'description']
    ordering_fields = ['created_at', 'scan_count', 'last_scanned_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return QRCodeCreateSerializer
        return QRCodeSerializer

    def create(self, request, *args, **kwargs):
        """
        Generate a new QR code.

        POST /api/qr-codes/
        Body: {
            "qr_type": "CUTTER",
            "title": "Cutter #12345",
            "description": "Production cutter serial XYZ",
            "content_type_id": 45,
            "object_id": 123,
            "size": 300
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Generate QR code
        try:
            from django.contrib.contenttypes.models import ContentType

            # Get related object if provided
            related_object = None
            if data.get('content_type_id') and data.get('object_id'):
                content_type = ContentType.objects.get(id=data['content_type_id'])
                model_class = content_type.model_class()
                related_object = model_class.objects.get(id=data['object_id'])

            qr_code = QRCodeService.generate_for_object(
                obj=related_object,
                qr_type=data['qr_type'],
                title=data.get('title', ''),
                description=data.get('description', ''),
                size=data.get('size', 300),
                expires_at=data.get('expires_at'),
                metadata=data.get('metadata', {})
            )

            output_serializer = QRCodeSerializer(qr_code, context={'request': request})
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def scan(self, request):
        """
        Scan a QR code and log the scan.

        POST /api/qr-codes/scan/
        Body: {
            "code": "QR-ABC123",
            "scan_context": "PRODUCTION",
            "latitude": 24.1234,
            "longitude": 55.5678,
            "device_info": {"model": "iPhone 13"},
            "metadata": {}
        }
        """
        serializer = QRScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Scan QR code
        try:
            gps_location = None
            if data.get('latitude') and data.get('longitude'):
                gps_location = {
                    'latitude': float(data['latitude']),
                    'longitude': float(data['longitude'])
                }

            related_object = QRCodeService.scan(
                code=data['code'],
                user=request.user,
                context=data.get('scan_context', 'INFO'),
                gps_location=gps_location,
                device_info=data.get('device_info'),
                metadata=data.get('metadata', {})
            )

            # Get the QR code
            qr_code = QRCode.objects.get(code=data['code'])

            # Return QR code info and related object
            return Response({
                'success': True,
                'qr_code': QRCodeSerializer(qr_code, context={'request': request}).data,
                'related_object': str(related_object) if related_object else None,
                'message': f'QR code {data["code"]} scanned successfully'
            })

        except QRCode.DoesNotExist:
            return Response(
                {'error': f'QR code "{data["code"]}" not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def scans(self, request, pk=None):
        """
        Get scan history for a QR code.

        GET /api/qr-codes/{id}/scans/
        """
        qr_code = self.get_object()
        scans = qr_code.scans.all().order_by('-scanned_at')

        page = self.paginate_queryset(scans)
        if page is not None:
            serializer = QRScanLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = QRScanLogSerializer(scans, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download QR code image.

        GET /api/qr-codes/{id}/download/
        """
        qr_code = self.get_object()

        if not qr_code.qr_image:
            return Response(
                {'error': 'QR code image not available'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Return image file
        response = HttpResponse(qr_code.qr_image.read(), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{qr_code.code}.png"'
        return response

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """
        Regenerate QR code image.

        POST /api/qr-codes/{id}/regenerate/
        Body: {
            "size": 500
        }
        """
        qr_code = self.get_object()
        size = request.data.get('size', 300)

        try:
            # Regenerate image
            from floor_app.operations.qr_system.services import QRCodeGenerator

            qr_image_file = QRCodeGenerator.generate_image(qr_code.code, size)
            qr_code.qr_image.save(f'{qr_code.code}.png', qr_image_file, save=True)

            serializer = self.get_serializer(qr_code, context={'request': request})
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get QR code statistics.

        GET /api/qr-codes/stats/
        """
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'by_type': list(
                queryset.values('qr_type').annotate(count=Count('id'))
            ),
            'by_status': list(
                queryset.values('status').annotate(count=Count('id'))
            ),
            'total_scans': sum(queryset.values_list('scan_count', flat=True)),
            'never_scanned': queryset.filter(scan_count=0).count(),
        }

        return Response(stats)


class QRBatchGenerationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing batch QR code generation.

    list: Get all batch generations
    retrieve: Get a specific batch
    create: Create a new batch generation
    """

    queryset = QRBatchGeneration.objects.all().prefetch_related('qr_codes')
    serializer_class = QRBatchGenerationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'qr_type']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return QRBatchGenerationCreateSerializer
        return QRBatchGenerationSerializer

    def create(self, request, *args, **kwargs):
        """
        Generate a batch of QR codes.

        POST /api/qr-batches/
        Body: {
            "batch_name": "Cutter Batch 2025-01",
            "qr_type": "CUTTER",
            "quantity": 100,
            "prefix": "CUT",
            "starting_number": 1001,
            "size": 300
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Create batch generation
        batch = QRBatchGeneration.objects.create(
            batch_name=data['batch_name'],
            qr_type=data['qr_type'],
            quantity=data['quantity'],
            prefix=data.get('prefix', 'QR'),
            starting_number=data.get('starting_number', 1),
            size=data.get('size', 300),
            created_by=request.user,
            metadata=data.get('metadata', {})
        )

        # Generate QR codes in background (or synchronously for now)
        try:
            batch.generate_codes()

            output_serializer = QRBatchGenerationSerializer(batch)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            batch.status = 'FAILED'
            batch.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def codes(self, request, pk=None):
        """
        Get all QR codes in this batch.

        GET /api/qr-batches/{id}/codes/
        """
        batch = self.get_object()
        codes = batch.qr_codes.all()

        page = self.paginate_queryset(codes)
        if page is not None:
            serializer = QRCodeSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = QRCodeSerializer(codes, many=True, context={'request': request})
        return Response(serializer.data)


class QRScanLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing QR scan logs (read-only).

    list: Get all scan logs
    retrieve: Get a specific scan log
    """

    queryset = QRScanLog.objects.all().select_related(
        'qr_code', 'scanned_by_user', 'scanned_by_employee'
    )
    serializer_class = QRScanLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['qr_code', 'scan_context', 'scanned_by_user']
    ordering = ['-scanned_at']

    def get_queryset(self):
        """Admin can see all scans, regular users see their own."""
        user = self.request.user

        if user.is_staff:
            return QRScanLog.objects.all()

        return QRScanLog.objects.filter(
            Q(scanned_by_user=user)
        ).select_related('qr_code', 'scanned_by_user', 'scanned_by_employee')

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent scans (last 24 hours).

        GET /api/qr-scans/recent/
        """
        from datetime import timedelta
        since = timezone.now() - timedelta(hours=24)

        queryset = self.get_queryset().filter(scanned_at__gte=since)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class QRPrintJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing QR print jobs.

    list: Get all print jobs
    retrieve: Get a specific print job
    create: Create a new print job
    """

    queryset = QRPrintJob.objects.all().prefetch_related('qr_codes')
    serializer_class = QRPrintJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'template']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Set printed_by to current user."""
        serializer.save(printed_by=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_printed(self, request, pk=None):
        """
        Mark print job as printed.

        POST /api/qr-print-jobs/{id}/mark_printed/
        """
        print_job = self.get_object()

        print_job.status = 'PRINTED'
        print_job.printed_at = timezone.now()
        print_job.save()

        serializer = self.get_serializer(print_job)
        return Response(serializer.data)


class QRTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing QR templates.

    list: Get all QR templates
    retrieve: Get a specific template
    create: Create a new template
    update: Update a template
    destroy: Delete a template
    """

    queryset = QRTemplate.objects.all()
    serializer_class = QRTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['template_type', 'paper_size', 'is_default']
    ordering = ['-is_default', 'name']
