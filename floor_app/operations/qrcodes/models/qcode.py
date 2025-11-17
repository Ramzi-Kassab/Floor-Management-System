"""
Central QCode model - Generic pointer using ContentType framework.

This is the core identity for all QR/barcode tokens in the system.
"""
import uuid
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.urls import reverse

from floor_app.mixins import AuditMixin


class QCodeType:
    """Constants for QCode types."""
    EMPLOYEE = 'EMPLOYEE'
    JOB_CARD = 'JOB_CARD'
    PROCESS_STEP = 'PROCESS_STEP'
    BIT_SERIAL = 'BIT_SERIAL'
    BIT_BOX = 'BIT_BOX'
    EQUIPMENT = 'EQUIPMENT'
    LOCATION = 'LOCATION'
    ADDRESS = 'ADDRESS'
    ITEM = 'ITEM'
    BOM_MATERIAL = 'BOM_MATERIAL'
    MAINTENANCE_REQUEST = 'MAINTENANCE_REQUEST'
    EVALUATION_SESSION = 'EVALUATION_SESSION'
    BATCH_ORDER = 'BATCH_ORDER'

    CHOICES = (
        (EMPLOYEE, 'Employee'),
        (JOB_CARD, 'Job Card'),
        (PROCESS_STEP, 'Process Step'),
        (BIT_SERIAL, 'Serial Unit (Bit)'),
        (BIT_BOX, 'Bit Box / Container'),
        (EQUIPMENT, 'Equipment'),
        (LOCATION, 'Location'),
        (ADDRESS, 'Address'),
        (ITEM, 'Item / Material'),
        (BOM_MATERIAL, 'BOM Material Pickup'),
        (MAINTENANCE_REQUEST, 'Maintenance Request'),
        (EVALUATION_SESSION, 'Evaluation Session'),
        (BATCH_ORDER, 'Batch Order'),
    )


class QCodeManager(models.Manager):
    """Custom manager for QCode."""

    def active(self):
        """Return only active QCodes."""
        return self.filter(is_active=True)

    def for_type(self, qcode_type):
        """Filter by QCode type."""
        return self.filter(qcode_type=qcode_type)

    def get_by_token(self, token):
        """Get QCode by token."""
        return self.get(token=token, is_active=True)

    def create_for_object(self, obj, qcode_type, label=None, created_by=None):
        """
        Create a QCode for any Django model instance.

        Args:
            obj: The target model instance
            qcode_type: One of QCodeType constants
            label: Optional human-readable label
            created_by: User who created this QCode

        Returns:
            QCode instance
        """
        content_type = ContentType.objects.get_for_model(obj)

        if not label:
            label = f"{qcode_type} - {str(obj)[:50]}"

        return self.create(
            qcode_type=qcode_type,
            content_type=content_type,
            object_id=obj.pk,
            label=label,
            created_by=created_by,
        )


class QCode(AuditMixin):
    """
    Central QR Code identity model using Generic Foreign Key.

    This model stores the mapping between a QR token and the target object
    (Employee, JobCard, ProcessStep, Equipment, SerialUnit, etc.).

    The token is a non-guessable UUID4, and the QR payload is a URL like:
    /q/<token>/ or /q/<type>/<token>/

    Security: The QR content must not include sensitive data directly.
    The token is an opaque key; all details are resolved server-side.
    """

    # Token is the unique identifier embedded in QR/barcode
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Unique non-guessable token embedded in QR code"
    )

    # Type describes the logical entity type
    qcode_type = models.CharField(
        max_length=30,
        choices=QCodeType.CHOICES,
        db_index=True,
        help_text="Type of entity this QCode points to"
    )

    # Generic Foreign Key to target object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='qcodes',
        help_text="Content type of target object"
    )
    object_id = models.BigIntegerField(
        db_index=True,
        help_text="Primary key of target object"
    )
    target_object = GenericForeignKey('content_type', 'object_id')

    # Human-readable label
    label = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Human-readable label for this QCode"
    )

    # Description/notes
    description = models.TextField(
        blank=True,
        default="",
        help_text="Optional description or notes"
    )

    # Active flag for quick revocation/disabling
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="If False, scans of this code will be rejected"
    )

    # Deactivation tracking
    deactivated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this QCode was deactivated"
    )
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deactivated_qcodes',
        help_text="User who deactivated this QCode"
    )
    deactivation_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for deactivation"
    )

    # Statistics
    scan_count = models.IntegerField(
        default=0,
        help_text="Total number of times this code has been scanned"
    )
    last_scanned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this code was scanned"
    )
    last_scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_scanned_qcodes',
        help_text="Last user who scanned this code"
    )

    # Code generation metadata
    code_format = models.CharField(
        max_length=20,
        choices=(
            ('QR', 'QR Code'),
            ('CODE128', 'Code 128'),
            ('CODE39', 'Code 39'),
            ('EAN13', 'EAN-13'),
            ('UPC', 'UPC-A'),
            ('DATAMATRIX', 'Data Matrix'),
        ),
        default='QR',
        help_text="Type of barcode/QR code"
    )

    # Version tracking (for regeneration)
    version = models.IntegerField(
        default=1,
        help_text="Version number, incremented on regeneration"
    )

    objects = QCodeManager()

    class Meta:
        db_table = 'qrcode_qcode'
        verbose_name = 'QR Code'
        verbose_name_plural = 'QR Codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token'], name='ix_qcode_token'),
            models.Index(fields=['qcode_type'], name='ix_qcode_type'),
            models.Index(fields=['is_active'], name='ix_qcode_active'),
            models.Index(fields=['content_type', 'object_id'], name='ix_qcode_target'),
            models.Index(fields=['last_scanned_at'], name='ix_qcode_last_scan'),
            models.Index(fields=['-created_at'], name='ix_qcode_created'),
        ]

    def __str__(self):
        return f"{self.get_qcode_type_display()} - {self.token_short}"

    @property
    def token_short(self):
        """Return shortened token for display."""
        return str(self.token)[:8]

    @property
    def token_str(self):
        """Return full token as string."""
        return str(self.token)

    def get_scan_url(self):
        """Get the URL that will be encoded in the QR code."""
        return reverse('qrcodes:scan', kwargs={'token': self.token_str})

    def get_absolute_url(self):
        """Get detail view URL."""
        return reverse('qrcodes:detail', kwargs={'token': self.token_str})

    def get_image_url(self, format='png'):
        """Get URL to QR code image."""
        return reverse('qrcodes:image', kwargs={
            'token': self.token_str,
            'format': format
        })

    def deactivate(self, user=None, reason=""):
        """Deactivate this QCode."""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.deactivated_by = user
        self.deactivation_reason = reason
        self.save(update_fields=[
            'is_active', 'deactivated_at', 'deactivated_by',
            'deactivation_reason', 'updated_at', 'updated_by'
        ])

    def reactivate(self, user=None):
        """Reactivate this QCode."""
        self.is_active = True
        self.deactivated_at = None
        self.deactivated_by = None
        self.deactivation_reason = ""
        self.version += 1
        self.save(update_fields=[
            'is_active', 'deactivated_at', 'deactivated_by',
            'deactivation_reason', 'version', 'updated_at', 'updated_by'
        ])

    def record_scan(self, user=None):
        """Update scan statistics."""
        self.scan_count += 1
        self.last_scanned_at = timezone.now()
        self.last_scanned_by = user
        self.save(update_fields=['scan_count', 'last_scanned_at', 'last_scanned_by'])

    def regenerate_token(self, user=None):
        """
        Generate a new token (invalidates old printed codes).

        Use this when a QR code is compromised or lost.
        """
        old_token = self.token
        self.token = uuid.uuid4()
        self.version += 1
        self.updated_by = user
        self.save(update_fields=['token', 'version', 'updated_at', 'updated_by'])
        return old_token, self.token

    @classmethod
    def get_or_create_for_object(cls, obj, qcode_type, label=None, created_by=None):
        """
        Get existing QCode for object or create a new one.

        Returns:
            Tuple of (qcode, created)
        """
        content_type = ContentType.objects.get_for_model(obj)

        qcode = cls.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
            qcode_type=qcode_type,
            is_active=True
        ).first()

        if qcode:
            return qcode, False

        return cls.objects.create_for_object(
            obj=obj,
            qcode_type=qcode_type,
            label=label,
            created_by=created_by
        ), True
