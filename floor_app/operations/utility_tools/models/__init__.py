"""
Utility Tools System

Comprehensive utility tools for common tasks:
- Image processing (resize, compress, format conversion)
- File conversion (PDF, Excel, CSV, etc.)
- Text tools (case conversion, formatting)
- PDF tools (merge, split, compress)
- Data conversion (JSON, XML, CSV)
- QR/Barcode generation
- Hash generators
- Color converters
- Unit converters
- Date/time tools
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from floor_app.mixins import AuditMixin


class ToolUsageLog(AuditMixin):
    """
    Track usage of utility tools for analytics and limits.
    """

    TOOL_CATEGORIES = (
        ('IMAGE', 'Image Tools'),
        ('FILE', 'File Conversion'),
        ('PDF', 'PDF Tools'),
        ('TEXT', 'Text Tools'),
        ('DATA', 'Data Conversion'),
        ('CODE', 'Code Generation'),
        ('CALCULATOR', 'Calculators'),
        ('CONVERTER', 'Unit Converters'),
    )

    TOOL_TYPES = (
        # Image Tools
        ('IMAGE_RESIZE', 'Image Resize'),
        ('IMAGE_COMPRESS', 'Image Compress'),
        ('IMAGE_FORMAT', 'Image Format Conversion'),
        ('IMAGE_CROP', 'Image Crop'),
        ('IMAGE_ROTATE', 'Image Rotate'),

        # File Conversion
        ('PDF_TO_WORD', 'PDF to Word'),
        ('WORD_TO_PDF', 'Word to PDF'),
        ('EXCEL_TO_CSV', 'Excel to CSV'),
        ('CSV_TO_EXCEL', 'CSV to Excel'),
        ('IMAGE_TO_PDF', 'Images to PDF'),

        # PDF Tools
        ('PDF_MERGE', 'PDF Merge'),
        ('PDF_SPLIT', 'PDF Split'),
        ('PDF_COMPRESS', 'PDF Compress'),
        ('PDF_ROTATE', 'PDF Rotate'),
        ('PDF_EXTRACT', 'PDF Extract Pages'),

        # Text Tools
        ('TEXT_CASE', 'Text Case Conversion'),
        ('TEXT_FORMAT', 'Text Formatting'),
        ('TEXT_COUNT', 'Word/Character Count'),
        ('TEXT_DIFF', 'Text Difference'),
        ('TEXT_ENCODE', 'Text Encoding'),

        # Data Conversion
        ('JSON_TO_XML', 'JSON to XML'),
        ('XML_TO_JSON', 'XML to JSON'),
        ('JSON_TO_CSV', 'JSON to CSV'),
        ('CSV_TO_JSON', 'CSV to JSON'),
        ('YAML_TO_JSON', 'YAML to JSON'),

        # Code Generation
        ('QR_CODE', 'QR Code Generator'),
        ('BARCODE', 'Barcode Generator'),
        ('UUID_GEN', 'UUID Generator'),
        ('PASSWORD_GEN', 'Password Generator'),
        ('HASH_GEN', 'Hash Generator'),

        # Calculators
        ('DATE_CALC', 'Date Calculator'),
        ('TIME_CALC', 'Time Calculator'),
        ('BUSINESS_DAYS', 'Business Days Calculator'),
        ('AGE_CALC', 'Age Calculator'),

        # Converters
        ('UNIT_LENGTH', 'Length Converter'),
        ('UNIT_WEIGHT', 'Weight Converter'),
        ('UNIT_TEMP', 'Temperature Converter'),
        ('UNIT_CURRENCY', 'Currency Converter'),
        ('COLOR_CONV', 'Color Converter'),
        ('BASE_CONV', 'Number Base Converter'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tool_usage_logs'
    )
    tool_category = models.CharField(max_length=20, choices=TOOL_CATEGORIES)
    tool_type = models.CharField(max_length=30, choices=TOOL_TYPES, db_index=True)

    # Input/Output tracking
    input_size_bytes = models.BigIntegerField(null=True, blank=True)
    output_size_bytes = models.BigIntegerField(null=True, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)

    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    # Metadata
    parameters = models.JSONField(
        default=dict,
        help_text="Tool parameters used"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata"
    )

    class Meta:
        db_table = 'utility_tools_usage_log'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['tool_type', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_tool_type_display()} at {self.created_at}"


class SavedConversion(AuditMixin):
    """
    Save frequently used conversions for quick access.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_conversions'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    tool_type = models.CharField(max_length=30, choices=ToolUsageLog.TOOL_TYPES)

    # Saved parameters
    parameters = models.JSONField(
        default=dict,
        help_text="Saved conversion parameters"
    )

    # Usage tracking
    use_count = models.PositiveIntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'utility_tools_saved_conversion'
        unique_together = [('user', 'name')]
        ordering = ['-last_used_at', 'name']

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def use(self):
        """Increment use count and update last used timestamp."""
        self.use_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['use_count', 'last_used_at'])


class ToolPreset(models.Model):
    """
    System-wide or user-defined presets for tools.
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    tool_type = models.CharField(max_length=30, choices=ToolUsageLog.TOOL_TYPES)

    # Preset parameters
    parameters = models.JSONField(
        default=dict,
        help_text="Preset parameters"
    )

    # System or user preset
    is_system_preset = models.BooleanField(
        default=False,
        help_text="System preset (available to all users)"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tool_presets'
    )

    # Ordering
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'utility_tools_preset'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


__all__ = ['ToolUsageLog', 'SavedConversion', 'ToolPreset']
