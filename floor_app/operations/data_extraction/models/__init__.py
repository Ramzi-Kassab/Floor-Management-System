"""Data Extraction Models - OCR & Import from Photos/PDF/Excel"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from floor_app.core.models import AuditMixin


class DataExtraction(AuditMixin):
    """Main data extraction job"""
    SOURCE_TYPES = (
        ('PHOTO', 'Photo/Image'),
        ('PDF', 'PDF Document'),
        ('EXCEL', 'Excel File'),
        ('CSV', 'CSV File'),
    )

    STATUS_CHOICES = (
        ('UPLOADED', 'File Uploaded'),
        ('PROCESSING', 'Processing'),
        ('EXTRACTED', 'Data Extracted'),
        ('MAPPED', 'Fields Mapped'),
        ('IMPORTED', 'Data Imported'),
        ('FAILED', 'Failed'),
    )

    extraction_number = models.CharField(max_length=50, unique=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='data_extractions'
    )

    # Source file
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    source_file = models.FileField(upload_to='data_extraction/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()

    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPLOADED')
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    # Extraction results
    raw_text = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict)  # Structured data
    detected_tables = models.JSONField(default=list)  # Tables detected
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Metadata
    total_fields_detected = models.IntegerField(default=0)
    total_rows_detected = models.IntegerField(default=0)

    # Target model (where to import)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    target_model_name = models.CharField(max_length=100, blank=True)

    # Import summary
    total_imported = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    import_errors = models.JSONField(default=list)

    # Settings
    ocr_language = models.CharField(max_length=10, default='eng')
    auto_detect_tables = models.BooleanField(default=True)
    auto_detect_headers = models.BooleanField(default=True)

    class Meta:
        db_table = 'data_extractions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'uploaded_by']),
            models.Index(fields=['source_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.extraction_number} - {self.get_source_type_display()}"


class ExtractedField(AuditMixin):
    """Individual field/column detected in extraction"""
    extraction = models.ForeignKey(
        DataExtraction,
        on_delete=models.CASCADE,
        related_name='fields'
    )

    # Field info
    field_name = models.CharField(max_length=200)
    field_type = models.CharField(max_length=50)  # text, number, date, boolean, etc.
    sample_values = models.JSONField(default=list)  # First few values
    total_values = models.IntegerField(default=0)
    null_count = models.IntegerField(default=0)

    # Position (for tables)
    column_index = models.IntegerField(null=True, blank=True)
    table_index = models.IntegerField(default=0)

    # Data type detection
    detected_as_number = models.BooleanField(default=False)
    detected_as_date = models.BooleanField(default=False)
    detected_as_email = models.BooleanField(default=False)
    detected_as_phone = models.BooleanField(default=False)
    detected_as_url = models.BooleanField(default=False)

    # Statistics
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    unique_values_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'extracted_fields'
        ordering = ['table_index', 'column_index']

    def __str__(self):
        return f"{self.extraction.extraction_number} - {self.field_name}"


class FieldMapping(AuditMixin):
    """Map extracted fields to system model fields"""
    MAPPING_TYPES = (
        ('DIRECT', 'Direct Mapping'),
        ('TRANSFORM', 'Transform & Map'),
        ('LOOKUP', 'Lookup Value'),
        ('CALCULATED', 'Calculated Field'),
        ('SKIP', 'Skip Field'),
    )

    extraction = models.ForeignKey(
        DataExtraction,
        on_delete=models.CASCADE,
        related_name='mappings'
    )
    extracted_field = models.ForeignKey(
        ExtractedField,
        on_delete=models.CASCADE,
        related_name='mappings'
    )

    # Target field
    target_model = models.CharField(max_length=100)
    target_field = models.CharField(max_length=100)
    target_field_type = models.CharField(max_length=50)

    # Mapping configuration
    mapping_type = models.CharField(max_length=20, choices=MAPPING_TYPES, default='DIRECT')
    transformation_rule = models.JSONField(default=dict)  # Rules for transformation
    default_value = models.CharField(max_length=255, blank=True)

    # Validation
    is_required = models.BooleanField(default=False)
    validation_rule = models.JSONField(default=dict)

    # Smart suggestions
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_auto_suggested = models.BooleanField(default=False)
    manually_reviewed = models.BooleanField(default=False)

    class Meta:
        db_table = 'field_mappings'
        unique_together = [['extraction', 'extracted_field', 'target_field']]

    def __str__(self):
        return f"{self.extracted_field.field_name} -> {self.target_model}.{self.target_field}"


class ImportHistory(AuditMixin):
    """Track individual import records"""
    extraction = models.ForeignKey(
        DataExtraction,
        on_delete=models.CASCADE,
        related_name='import_records'
    )

    # Source data
    row_index = models.IntegerField()
    source_data = models.JSONField(default=dict)

    # Target record
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey('target_content_type', 'target_object_id')

    # Status
    import_status = models.CharField(
        max_length=20,
        choices=[
            ('SUCCESS', 'Success'),
            ('FAILED', 'Failed'),
            ('SKIPPED', 'Skipped'),
        ],
        default='SUCCESS'
    )
    error_message = models.TextField(blank=True)

    # Transformation applied
    transformed_data = models.JSONField(default=dict)

    class Meta:
        db_table = 'import_history'
        ordering = ['row_index']
        indexes = [
            models.Index(fields=['extraction', 'import_status']),
        ]

    def __str__(self):
        return f"Row {self.row_index} - {self.import_status}"


class DataExtractionTemplate(AuditMixin):
    """Reusable extraction templates for common documents"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='extraction_templates'
    )

    # Template settings
    source_type = models.CharField(max_length=20, choices=DataExtraction.SOURCE_TYPES)
    target_model = models.CharField(max_length=100)

    # Saved field mappings
    field_mappings = models.JSONField(default=dict)
    transformation_rules = models.JSONField(default=dict)

    # OCR/Extraction settings
    ocr_settings = models.JSONField(default=dict)
    preprocessing_steps = models.JSONField(default=list)

    # Usage tracking
    usage_count = models.IntegerField(default=0)
    success_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    is_shared = models.BooleanField(default=False)

    class Meta:
        db_table = 'data_extraction_templates'
        ordering = ['-usage_count', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class OCRProcessingLog(AuditMixin):
    """Detailed OCR processing logs"""
    extraction = models.ForeignKey(
        DataExtraction,
        on_delete=models.CASCADE,
        related_name='processing_logs'
    )

    # Processing step
    step_name = models.CharField(max_length=100)
    step_status = models.CharField(
        max_length=20,
        choices=[
            ('STARTED', 'Started'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
        ]
    )

    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True
    )

    # Details
    details = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'ocr_processing_logs'
        ordering = ['started_at']

    def __str__(self):
        return f"{self.extraction.extraction_number} - {self.step_name}"


class SmartFieldSuggestion(AuditMixin):
    """AI/ML suggestions for field mapping"""
    extracted_field = models.ForeignKey(
        ExtractedField,
        on_delete=models.CASCADE,
        related_name='suggestions'
    )

    # Suggestion
    suggested_model = models.CharField(max_length=100)
    suggested_field = models.CharField(max_length=100)
    confidence = models.DecimalField(max_digits=5, decimal_places=2)

    # Reasoning
    reason = models.TextField(blank=True)
    matching_factors = models.JSONField(default=list)

    # User feedback
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    class Meta:
        db_table = 'smart_field_suggestions'
        ordering = ['-confidence']

    def __str__(self):
        return f"{self.suggested_model}.{self.suggested_field} ({self.confidence}%)"
