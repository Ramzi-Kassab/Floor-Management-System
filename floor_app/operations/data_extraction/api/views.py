"""Data Extraction API Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.apps import apps
from ..models import (
    DataExtraction, ExtractedField, FieldMapping, ImportHistory,
    DataExtractionTemplate, SmartFieldSuggestion
)
from ..services.extraction_service import ExtractionService
from .serializers import (
    DataExtractionSerializer, DataExtractionCreateSerializer,
    ExtractedFieldSerializer, FieldMappingSerializer,
    ImportHistorySerializer, DataExtractionTemplateSerializer,
    ProcessExtractionSerializer, CreateMappingSerializer,
    BulkCreateMappingsSerializer, ExecuteImportSerializer,
    AcceptSuggestionSerializer, GetAvailableFieldsSerializer,
    SmartFieldSuggestionSerializer
)


class DataExtractionViewSet(viewsets.ModelViewSet):
    """Data extraction management"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return DataExtractionCreateSerializer
        return DataExtractionSerializer

    def get_queryset(self):
        """Get extractions for current user"""
        queryset = DataExtraction.objects.filter(
            uploaded_by=self.request.user
        ).prefetch_related('fields', 'mappings')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by source type
        source_type = self.request.query_params.get('source_type')
        if source_type:
            queryset = queryset.filter(source_type=source_type)

        return queryset.order_by('-created_at')

    def create(self, request):
        """Upload a file for extraction"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source_file = serializer.validated_data['source_file']

        extraction = ExtractionService.create_extraction(
            uploaded_by=request.user,
            source_type=serializer.validated_data['source_type'],
            source_file=source_file,
            original_filename=source_file.name,
            file_size=source_file.size,
            ocr_language=serializer.validated_data.get('ocr_language', 'eng'),
            auto_detect_tables=serializer.validated_data.get('auto_detect_tables', True),
            auto_detect_headers=serializer.validated_data.get('auto_detect_headers', True)
        )

        # Set target model if provided
        if serializer.validated_data.get('target_model_name'):
            extraction.target_model_name = serializer.validated_data['target_model_name']
            extraction.save(update_fields=['target_model_name'])

        return Response(
            DataExtractionSerializer(extraction).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process the uploaded file to extract data"""
        extraction = self.get_object()

        if extraction.status not in ['UPLOADED', 'FAILED']:
            return Response(
                {'error': 'Extraction already processed or in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            extraction = ExtractionService.process_extraction(extraction)
            return Response(DataExtractionSerializer(extraction).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def fields(self, request, pk=None):
        """Get extracted fields"""
        extraction = self.get_object()
        fields = extraction.fields.all()
        return Response(ExtractedFieldSerializer(fields, many=True).data)

    @action(detail=True, methods=['get'])
    def mappings(self, request, pk=None):
        """Get field mappings"""
        extraction = self.get_object()
        mappings = extraction.mappings.all()
        return Response(FieldMappingSerializer(mappings, many=True).data)

    @action(detail=True, methods=['post'])
    def create_mapping(self, request, pk=None):
        """Create a field mapping"""
        extraction = self.get_object()
        serializer = CreateMappingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            mapping = ExtractionService.create_field_mapping(
                extraction=extraction,
                extracted_field_id=serializer.validated_data['extracted_field_id'],
                target_model=serializer.validated_data['target_model'],
                target_field=serializer.validated_data['target_field'],
                mapping_type=serializer.validated_data.get('mapping_type', 'DIRECT'),
                transformation_rule=serializer.validated_data.get('transformation_rule', {}),
                default_value=serializer.validated_data.get('default_value', ''),
                is_required=serializer.validated_data.get('is_required', False),
                validation_rule=serializer.validated_data.get('validation_rule', {})
            )

            return Response(
                FieldMappingSerializer(mapping).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def bulk_create_mappings(self, request, pk=None):
        """Create multiple field mappings at once"""
        extraction = self.get_object()
        serializer = BulkCreateMappingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_mappings = []

        for mapping_data in serializer.validated_data['mappings']:
            try:
                mapping = ExtractionService.create_field_mapping(
                    extraction=extraction,
                    extracted_field_id=mapping_data['extracted_field_id'],
                    target_model=mapping_data['target_model'],
                    target_field=mapping_data['target_field'],
                    mapping_type=mapping_data.get('mapping_type', 'DIRECT'),
                    transformation_rule=mapping_data.get('transformation_rule', {}),
                    default_value=mapping_data.get('default_value', ''),
                    is_required=mapping_data.get('is_required', False),
                    validation_rule=mapping_data.get('validation_rule', {})
                )
                created_mappings.append(mapping)
            except Exception as e:
                # Continue with other mappings even if one fails
                pass

        return Response(
            FieldMappingSerializer(created_mappings, many=True).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def execute_import(self, request, pk=None):
        """Execute the data import"""
        extraction = self.get_object()

        try:
            extraction = ExtractionService.execute_import(extraction)
            return Response(DataExtractionSerializer(extraction).data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def import_history(self, request, pk=None):
        """Get import history for extraction"""
        extraction = self.get_object()

        # Filter by status
        status_filter = request.query_params.get('status')
        history = extraction.import_records.all()

        if status_filter:
            history = history.filter(import_status=status_filter)

        return Response(ImportHistorySerializer(history, many=True).data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get extraction statistics"""
        extraction = self.get_object()
        stats = ExtractionService.get_extraction_statistics(extraction)
        return Response(stats)

    @action(detail=True, methods=['post'])
    def accept_suggestion(self, request, pk=None):
        """Accept a smart field suggestion and create mapping"""
        extraction = self.get_object()
        serializer = AcceptSuggestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        suggestion = get_object_or_404(
            SmartFieldSuggestion,
            id=serializer.validated_data['suggestion_id']
        )

        # Create mapping from suggestion
        try:
            mapping = ExtractionService.create_field_mapping(
                extraction=extraction,
                extracted_field_id=suggestion.extracted_field_id,
                target_model=suggestion.suggested_model,
                target_field=suggestion.suggested_field,
                mapping_type='DIRECT'
            )

            # Mark suggestion as accepted
            suggestion.accepted = True
            suggestion.save(update_fields=['accepted'])

            return Response(FieldMappingSerializer(mapping).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def get_available_fields(self, request):
        """Get available fields for a model"""
        serializer = GetAvailableFieldsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        model_name = serializer.validated_data['model_name']

        try:
            model = apps.get_model(model_name)
        except LookupError:
            return Response(
                {'error': 'Model not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        fields = []
        for field in model._meta.get_fields():
            if not field.many_to_many and not field.one_to_many:
                fields.append({
                    'name': field.name,
                    'type': field.get_internal_type(),
                    'required': not field.null and not field.blank,
                    'help_text': getattr(field, 'help_text', '')
                })

        return Response({'model': model_name, 'fields': fields})


class DataExtractionTemplateViewSet(viewsets.ModelViewSet):
    """Data extraction template management"""
    serializer_class = DataExtractionTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get templates for current user or shared templates"""
        return DataExtractionTemplate.objects.filter(
            created_by=self.request.user
        ) | DataExtractionTemplate.objects.filter(is_shared=True)

    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def apply_template(self, request, pk=None):
        """Apply template to an extraction"""
        template = self.get_object()
        extraction_id = request.data.get('extraction_id')

        if not extraction_id:
            return Response(
                {'error': 'extraction_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        extraction = get_object_or_404(DataExtraction, id=extraction_id)

        # Apply template mappings
        created_mappings = []

        for field_name, mapping_config in template.field_mappings.items():
            # Find matching extracted field
            extracted_field = extraction.fields.filter(field_name=field_name).first()

            if extracted_field:
                try:
                    mapping = ExtractionService.create_field_mapping(
                        extraction=extraction,
                        extracted_field_id=extracted_field.id,
                        target_model=template.target_model,
                        target_field=mapping_config['target_field'],
                        mapping_type=mapping_config.get('mapping_type', 'DIRECT'),
                        transformation_rule=mapping_config.get('transformation_rule', {}),
                        default_value=mapping_config.get('default_value', ''),
                        is_required=mapping_config.get('is_required', False)
                    )
                    created_mappings.append(mapping)
                except Exception:
                    pass

        # Update usage count
        template.usage_count += 1
        template.save(update_fields=['usage_count'])

        return Response(
            FieldMappingSerializer(created_mappings, many=True).data,
            status=status.HTTP_201_CREATED
        )


class ExtractedFieldViewSet(viewsets.ReadOnlyModelViewSet):
    """Extracted field view (read-only)"""
    serializer_class = ExtractedFieldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get fields from user's extractions"""
        return ExtractedField.objects.filter(
            extraction__uploaded_by=self.request.user
        ).select_related('extraction')


class FieldMappingViewSet(viewsets.ModelViewSet):
    """Field mapping management"""
    serializer_class = FieldMappingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get mappings from user's extractions"""
        return FieldMapping.objects.filter(
            extraction__uploaded_by=self.request.user
        ).select_related('extraction', 'extracted_field')
