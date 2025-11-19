"""
QR Code System for Production, Inventory, and Logistics

Universal QR code system that can be attached to any object:
- Cutters (serial units)
- PDC Bits (finished products)
- Locations (warehouses, shelves, bins)
- Employees (ID badges)
- Job Cards (work orders)
- Deliveries/Shipments
- Packages/Containers
- Equipment/Tools

Features:
- Generate QR codes for any object
- Scan and decode QR codes
- Track scan history (who, when, where, why)
- GPS location capture on scan
- Context-aware actions (different behavior based on scan context)
- Integration with GPS verification
- Integration with employee device tracking
- Expiry and deactivation
- QR code versioning
- Print-ready QR images
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings
import uuid
import hashlib

from floor_app.mixins import AuditMixin


class QRCode(AuditMixin):
    """
    Universal QR code model.

    Can be linked to any object via GenericForeignKey.
    """

    QR_TYPES = (
        ('CUTTER', 'Cutter (Serial Unit)'),
        ('BIT', 'PDC Bit (Finished Product)'),
        ('LOCATION', 'Storage Location'),
        ('EMPLOYEE', 'Employee ID Badge'),
        ('JOB_CARD', 'Job Card / Work Order'),
        ('DELIVERY', 'Delivery / Shipment'),
        ('PACKAGE', 'Package / Container'),
        ('EQUIPMENT', 'Equipment / Tool'),
        ('BOM', 'Bill of Materials'),
        ('CUSTOM', 'Custom'),
    )

    # Unique QR code value
    code = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text="The QR code value (unique identifier)"
    )

    # QR code type
    qr_type = models.CharField(
        max_length=20,
        choices=QR_TYPES,
        db_index=True
    )

    # Linked object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')

    # QR code image
    qr_image = models.ImageField(
        upload_to='qr_codes/%Y/%m/',
        null=True,
        blank=True,
        help_text="Generated QR code image"
    )
    qr_size = models.PositiveIntegerField(
        default=300,
        help_text="QR code image size in pixels"
    )

    # Metadata
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Human-readable title for this QR code"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this QR code is for"
    )

    # Usage tracking
    scan_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of scans"
    )
    last_scanned_at = models.DateTimeField(
        null=True,
        blank=True
    )
    last_scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_scanned_qr_codes'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Is this QR code active?"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Expiry date (optional, for time-limited QR codes)"
    )
    deactivated_at = models.DateTimeField(
        null=True,
        blank=True
    )
    deactivation_reason = models.TextField(blank=True)

    # Versioning (for regenerated QR codes)
    version = models.PositiveIntegerField(
        default=1,
        help_text="QR code version (increments on regeneration)"
    )
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions'
    )

    # Print tracking
    print_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this QR code has been printed"
    )
    last_printed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'qr_codes_qrcode'
        indexes = [
            models.Index(fields=['qr_type', 'is_active']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-last_scanned_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_qr_type_display()}: {self.code}"

    @property
    def is_expired(self):
        """Check if QR code has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_valid(self):
        """Check if QR code is valid for scanning."""
        return self.is_active and not self.is_expired

    def increment_scan_count(self, user=None):
        """Increment scan count and update last scanned info."""
        self.scan_count += 1
        self.last_scanned_at = timezone.now()
        if user:
            self.last_scanned_by = user
        self.save(update_fields=['scan_count', 'last_scanned_at', 'last_scanned_by'])

    def increment_print_count(self):
        """Increment print count."""
        self.print_count += 1
        self.last_printed_at = timezone.now()
        self.save(update_fields=['print_count', 'last_printed_at'])

    def deactivate(self, reason=''):
        """Deactivate this QR code."""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.deactivation_reason = reason
        self.save(update_fields=['is_active', 'deactivated_at', 'deactivation_reason'])

    @classmethod
    def generate_code(cls, prefix='QR'):
        """
        Generate a unique QR code value.

        Format: PREFIX-TIMESTAMP-HASH
        Example: QR-20250118-A3F9D2
        """
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_uuid = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{timestamp}-{random_uuid}"


class QRScanLog(models.Model):
    """
    Log every QR code scan.

    Tracks who scanned, when, where (GPS), and in what context.
    """

    SCAN_CONTEXTS = (
        ('RECEIVING', 'Receiving / Incoming Inspection'),
        ('PRODUCTION', 'Production / Assembly'),
        ('QC', 'Quality Control'),
        ('NDT', 'NDT Inspection'),
        ('REWORK', 'Rework'),
        ('SHIPPING', 'Shipping / Outgoing'),
        ('INVENTORY_CHECK', 'Inventory Stock Check'),
        ('LOCATION_VERIFY', 'Location Verification'),
        ('EMPLOYEE_CHECKIN', 'Employee Check-in'),
        ('DELIVERY', 'Delivery Confirmation'),
        ('TRANSFER', 'Stock Transfer'),
        ('INFO', 'Information Lookup'),
        ('OTHER', 'Other'),
    )

    # QR code that was scanned
    qr_code = models.ForeignKey(
        QRCode,
        on_delete=models.CASCADE,
        related_name='scan_logs'
    )

    # Who scanned
    scanned_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qr_scans'
    )
    scanned_by_employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qr_scans'
    )

    # When
    scanned_at = models.DateTimeField(auto_now_add=True)

    # Where (GPS)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="GPS latitude"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="GPS longitude"
    )
    gps_accuracy_meters = models.FloatField(
        null=True,
        blank=True,
        help_text="GPS accuracy in meters"
    )
    location_address = models.CharField(
        max_length=500,
        blank=True,
        help_text="Reverse-geocoded address"
    )

    # Context
    scan_context = models.CharField(
        max_length=30,
        choices=SCAN_CONTEXTS,
        default='INFO'
    )

    # Device info
    device_info = models.JSONField(
        default=dict,
        help_text="Device information (model, OS, app version, etc.)"
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional scan metadata"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about this scan"
    )

    # Action taken after scan
    action_taken = models.CharField(
        max_length=100,
        blank=True,
        help_text="What action was taken after scanning (e.g., 'Added to map cell', 'Verified location')"
    )

    class Meta:
        db_table = 'qr_codes_scanlog'
        indexes = [
            models.Index(fields=['qr_code', '-scanned_at']),
            models.Index(fields=['scanned_by_user', '-scanned_at']),
            models.Index(fields=['scanned_by_employee', '-scanned_at']),
            models.Index(fields=['scan_context', '-scanned_at']),
            models.Index(fields=['-scanned_at']),
        ]
        ordering = ['-scanned_at']

    def __str__(self):
        scanner = self.scanned_by_user or self.scanned_by_employee or 'Unknown'
        return f"{self.qr_code.code} scanned by {scanner} at {self.scanned_at}"

    @property
    def has_gps_location(self):
        """Check if scan has GPS coordinates."""
        return self.latitude is not None and self.longitude is not None


class QRBatch(AuditMixin):
    """
    Batch of QR codes generated together.

    Useful for bulk generation (e.g., generate 100 QR codes for new cutters).
    """

    batch_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Batch number for tracking"
    )
    qr_type = models.CharField(
        max_length=20,
        choices=QRCode.QR_TYPES
    )

    # Batch info
    quantity = models.PositiveIntegerField(
        help_text="Number of QR codes in this batch"
    )
    generated_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of QR codes actually generated"
    )

    # Purpose
    purpose = models.TextField(
        blank=True,
        help_text="Purpose of this batch"
    )

    # Status
    is_complete = models.BooleanField(
        default=False,
        help_text="Has batch generation completed?"
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    # Print tracking
    is_printed = models.BooleanField(
        default=False,
        help_text="Has this batch been printed?"
    )
    printed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'qr_codes_batch'
        verbose_name_plural = 'QR Batches'
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch {self.batch_number}: {self.quantity} {self.get_qr_type_display()} QR codes"


class QRCodePrintJob(models.Model):
    """
    Track QR code print jobs.

    Records when QR codes are printed, for what purpose, and by whom.
    """

    PRINT_FORMATS = (
        ('LABEL_SMALL', 'Small Label (40mm x 40mm)'),
        ('LABEL_MEDIUM', 'Medium Label (70mm x 70mm)'),
        ('LABEL_LARGE', 'Large Label (100mm x 100mm)'),
        ('SHEET_A4', 'A4 Sheet (multiple QR codes)'),
        ('SHEET_LETTER', 'Letter Sheet (multiple QR codes)'),
        ('BADGE', 'ID Badge Format'),
        ('CUSTOM', 'Custom Format'),
    )

    # What was printed
    qr_codes = models.ManyToManyField(
        QRCode,
        related_name='print_jobs'
    )
    batch = models.ForeignKey(
        QRBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='print_jobs'
    )

    # Print details
    print_format = models.CharField(
        max_length=20,
        choices=PRINT_FORMATS
    )
    copies = models.PositiveIntegerField(
        default=1,
        help_text="Number of copies printed"
    )

    # Who printed
    printed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    printed_at = models.DateTimeField(auto_now_add=True)

    # Purpose
    purpose = models.TextField(
        blank=True,
        help_text="Why these QR codes were printed"
    )

    # Output
    pdf_file = models.FileField(
        upload_to='qr_prints/%Y/%m/',
        null=True,
        blank=True,
        help_text="Generated PDF file"
    )

    class Meta:
        db_table = 'qr_codes_printjob'
        ordering = ['-printed_at']

    def __str__(self):
        count = self.qr_codes.count()
        return f"Print job: {count} QR codes on {self.printed_at.date()}"


class QRCodeTemplate(models.Model):
    """
    Templates for generating QR code labels.

    Define layout, size, and design for different QR code print formats.
    """

    name = models.CharField(
        max_length=100,
        unique=True
    )
    qr_type = models.CharField(
        max_length=20,
        choices=QRCode.QR_TYPES,
        help_text="Default QR type for this template"
    )

    # Dimensions (in mm)
    width_mm = models.FloatField(help_text="Label width in mm")
    height_mm = models.FloatField(help_text="Label height in mm")
    qr_size_mm = models.FloatField(help_text="QR code size in mm")

    # Layout configuration
    layout_config = models.JSONField(
        default=dict,
        help_text="Layout configuration (margins, padding, fonts, etc.)"
    )

    # Template file
    template_file = models.FileField(
        upload_to='qr_templates/',
        null=True,
        blank=True,
        help_text="Custom template file (HTML/PDF)"
    )

    # Preview
    preview_image = models.ImageField(
        upload_to='qr_templates/previews/',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'qr_codes_template'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.width_mm}x{self.height_mm}mm)"
