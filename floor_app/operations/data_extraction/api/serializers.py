"""Data Extraction API Serializers"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import (
    DataExtraction, ExtractedField, FieldMapping, ImportHistory,
    DataExtractionTemplate, SmartFieldSuggestion
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']
        read_only_fields = fields


class SmartFieldSuggestionSerializer(serializers.ModelSerializer):
    """Smart field suggestion serializer"""

    class Meta:
        model = SmartFieldSuggestion
        fields = [
            'id', 'suggested_model', 'suggested_field', 'confidence',
            'reason', 'matching_factors', 'accepted', 'rejected'
        ]
        read_only_fields = ['id', 'confidence', 'reason', 'matching_factors']


class ExtractedFieldSerializer(serializers.ModelSerializer):
    """Extracted field serializer"""
    suggestions = SmartFieldSuggestionSerializer(many=True, read_only=True)

    class Meta:
        model = ExtractedField
        fields = [
            'id', 'field_name', 'field_type', 'sample_values', 'total_values',
            'null_count', 'column_index', 'table_index', 'detected_as_number',
            'detected_as_date', 'detected_as_email', 'detected_as_phone',
            'detected_as_url', 'min_length', 'max_length', 'unique_values_count',
            'suggestions'
        ]
        read_only_fields = fields


class FieldMappingSerializer(serializers.ModelSerializer):
    """Field mapping serializer"""
    extracted_field = ExtractedFieldSerializer(read_only=True)
    extracted_field_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FieldMapping
        fields = [
            'id', 'extracted_field', 'extracted_field_id', 'target_model',
            'target_field', 'target_field_type', 'mapping_type',
            'transformation_rule', 'default_value', 'is_required',
            'validation_rule', 'confidence_score', 'is_auto_suggested',
            'manually_reviewed'
        ]
        read_only_fields = ['id', 'target_field_type', 'confidence_score', 'is_auto_suggested']


class ImportHistorySerializer(serializers.ModelSerializer):
    """Import history serializer"""

    class Meta:
        model = ImportHistory
        fields = [
            'id', 'row_index', 'source_data', 'target_object_id',
            'import_status', 'error_message', 'transformed_data', 'created_at'
        ]
        read_only_fields = fields


class DataExtractionSerializer(serializers.ModelSerializer):
    """Data extraction serializer"""
    uploaded_by = UserBasicSerializer(read_only=True)
    fields = ExtractedFieldSerializer(many=True, read_only=True)
    mappings = FieldMappingSerializer(many=True, read_only=True)
    field_count = serializers.IntegerField(source='fields.count', read_only=True)
    mapping_count = serializers.IntegerField(source='mappings.count', read_only=True)

    class Meta:
        model = DataExtraction
        fields = [
            'id', 'extraction_number', 'uploaded_by', 'source_type', 'source_file',
            'original_filename', 'file_size', 'status', 'processing_started_at',
            'processing_completed_at', 'raw_text', 'extracted_data', 'detected_tables',
            'confidence_score', 'total_fields_detected', 'total_rows_detected',
            'target_model_name', 'total_imported', 'total_failed', 'import_errors',
            'ocr_language', 'auto_detect_tables', 'auto_detect_headers',
            'fields', 'mappings', 'field_count', 'mapping_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'extraction_number', 'uploaded_by', 'status', 'processing_started_at',
            'processing_completed_at', 'raw_text', 'extracted_data', 'detected_tables',
            'confidence_score', 'total_fields_detected', 'total_rows_detected',
            'total_imported', 'total_failed', 'import_errors', 'fields', 'mappings',
            'field_count', 'mapping_count', 'created_at', 'updated_at'
        ]


class DataExtractionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating data extraction"""

    class Meta:
        model = DataExtraction
        fields = [
            'source_type', 'source_file', 'ocr_language', 'auto_detect_tables',
            'auto_detect_headers', 'target_model_name'
        ]

    def validate_source_file(self, value):
        """Validate file size and type"""
        # Max 50MB
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 50MB")

        return value


class DataExtractionTemplateSerializer(serializers.ModelSerializer):
    """Data extraction template serializer"""
    created_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = DataExtractionTemplate
        fields = [
            'id', 'name', 'description', 'created_by', 'source_type',
            'target_model', 'field_mappings', 'transformation_rules',
            'ocr_settings', 'preprocessing_steps', 'usage_count',
            'success_rate', 'is_active', 'is_shared', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'usage_count', 'success_rate', 'created_at', 'updated_at']


class ProcessExtractionSerializer(serializers.Serializer):
    """Serializer for processing extraction"""
    pass  # No input needed


class CreateMappingSerializer(serializers.Serializer):
    """Serializer for creating field mapping"""
    extracted_field_id = serializers.IntegerField(required=True)
    target_model = serializers.CharField(required=True, max_length=100)
    target_field = serializers.CharField(required=True, max_length=100)
    mapping_type = serializers.ChoiceField(
        choices=FieldMapping.MAPPING_TYPES,
        default='DIRECT'
    )
    transformation_rule = serializers.JSONField(default=dict)
    default_value = serializers.CharField(required=False, allow_blank=True)
    is_required = serializers.BooleanField(default=False)
    validation_rule = serializers.JSONField(default=dict)


class BulkCreateMappingsSerializer(serializers.Serializer):
    """Serializer for creating multiple mappings at once"""
    mappings = serializers.ListField(
        child=CreateMappingSerializer(),
        min_length=1
    )


class ExecuteImportSerializer(serializers.Serializer):
    """Serializer for executing import"""
    pass  # No input needed


class AcceptSuggestionSerializer(serializers.Serializer):
    """Serializer for accepting a field suggestion"""
    suggestion_id = serializers.IntegerField(required=True)


class GetAvailableFieldsSerializer(serializers.Serializer):
    """Serializer for getting available model fields"""
    model_name = serializers.CharField(required=True, max_length=100)
