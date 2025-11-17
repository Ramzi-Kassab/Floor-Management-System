"""
ScanLog model - Comprehensive audit trail for all QR/barcode scans.

Records WHO, WHAT, WHEN, WHERE, WHY for every scan event.
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class ScanActionType:
    """Constants for scan action types."""
    VIEW_DETAILS = 'VIEW_DETAILS'
    PROCESS_START = 'PROCESS_START'
    PROCESS_END = 'PROCESS_END'
    PROCESS_PAUSE = 'PROCESS_PAUSE'
    PROCESS_RESUME = 'PROCESS_RESUME'
    MOVE_ITEM = 'MOVE_ITEM'
    MAINTENANCE_REPORT = 'MAINTENANCE_REPORT'
    MAINTENANCE_COMPLETE = 'MAINTENANCE_COMPLETE'
    CHECK_IN = 'CHECK_IN'
    CHECK_OUT = 'CHECK_OUT'
    BADGE_ACCESS = 'BADGE_ACCESS'
    MATERIAL_PICKUP = 'MATERIAL_PICKUP'
    MATERIAL_RETURN = 'MATERIAL_RETURN'
    INVENTORY_COUNT = 'INVENTORY_COUNT'
    LOCATION_ASSIGN = 'LOCATION_ASSIGN'
    QUALITY_CHECK = 'QUALITY_CHECK'
    APPROVAL_SCAN = 'APPROVAL_SCAN'
    UNKNOWN = 'UNKNOWN'

    CHOICES = (
        (VIEW_DETAILS, 'View Details'),
        (PROCESS_START, 'Start Process Step'),
        (PROCESS_END, 'End Process Step'),
        (PROCESS_PAUSE, 'Pause Process Step'),
        (PROCESS_RESUME, 'Resume Process Step'),
        (MOVE_ITEM, 'Move Item to Location'),
        (MAINTENANCE_REPORT, 'Report Maintenance Issue'),
        (MAINTENANCE_COMPLETE, 'Mark Maintenance Complete'),
        (CHECK_IN, 'Check In'),
        (CHECK_OUT, 'Check Out'),
        (BADGE_ACCESS, 'Badge Access Control'),
        (MATERIAL_PICKUP, 'Material Pickup from BOM'),
        (MATERIAL_RETURN, 'Material Return to Stock'),
        (INVENTORY_COUNT, 'Inventory Count/Verification'),
        (LOCATION_ASSIGN, 'Assign to Location'),
        (QUALITY_CHECK, 'Quality Check/Inspection'),
        (APPROVAL_SCAN, 'Approval/Authorization Scan'),
        (UNKNOWN, 'Unknown Action'),
    )


class ScanLogManager(models.Manager):
    """Custom manager for ScanLog."""

    def for_qcode(self, qcode):
        """Get all scans for a specific QCode."""
        return self.filter(qcode=qcode).order_by('-scan_timestamp')

    def for_user(self, user):
        """Get all scans by a specific user."""
        return self.filter(scanner_user=user).order_by('-scan_timestamp')

    def for_action(self, action_type):
        """Get all scans of a specific action type."""
        return self.filter(action_type=action_type).order_by('-scan_timestamp')

    def successful(self):
        """Get only successful scans."""
        return self.filter(success=True)

    def failed(self):
        """Get only failed scans."""
        return self.filter(success=False)

    def today(self):
        """Get scans from today."""
        today = timezone.now().date()
        return self.filter(scan_timestamp__date=today)

    def recent(self, hours=24):
        """Get scans from last N hours."""
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        return self.filter(scan_timestamp__gte=cutoff)


class ScanLog(models.Model):
    """
    Comprehensive scan log capturing WHO/WHAT/WHEN/WHERE/WHY.

    This is a critical audit trail for:
    - Compliance and traceability
    - KPI calculation
    - Security auditing
    - Process monitoring
    """

    # WHAT was scanned
    qcode = models.ForeignKey(
        'qrcodes.QCode',
        on_delete=models.CASCADE,
        related_name='scan_logs',
        help_text="The QCode that was scanned"
    )

    # Action type - what did this scan do?
    action_type = models.CharField(
        max_length=30,
        choices=ScanActionType.CHOICES,
        db_index=True,
        help_text="The type of action performed"
    )

    # WHEN - timestamp of scan
    scan_timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the scan occurred"
    )

    # WHO - scanner identification
    scanner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qcode_scans',
        help_text="User who performed the scan"
    )

    # Link to HR Employee (for reporting)
    scanner_employee_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="HR Employee ID of scanner (cached)"
    )
    scanner_employee_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Employee name at time of scan"
    )

    # Device identification
    scanner_device_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Device/scanner hardware ID"
    )
    scanner_device_type = models.CharField(
        max_length=50,
        choices=(
            ('WEB', 'Web Browser'),
            ('MOBILE', 'Mobile Device'),
            ('HANDHELD', 'Handheld Scanner'),
            ('KIOSK', 'Kiosk Terminal'),
            ('API', 'API Call'),
            ('UNKNOWN', 'Unknown'),
        ),
        default='WEB',
        help_text="Type of device used for scanning"
    )

    # WHERE - location information
    scanner_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of scanner"
    )

    scanner_location_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Location ID where scan occurred"
    )
    scanner_location_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Location name at time of scan"
    )

    # GPS coordinates (for mobile scans)
    scanner_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="GPS latitude"
    )
    scanner_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="GPS longitude"
    )

    # Context - relation to other objects
    context_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scan_contexts',
        help_text="Content type of context object"
    )
    context_object_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID of context object"
    )
    context_object = GenericForeignKey('context_content_type', 'context_object_id')

    # WHY - reason for scan
    reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for this scan (e.g., pause reason, exception note)"
    )

    # Result
    success = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether the scan completed its intended action"
    )

    message = models.TextField(
        blank=True,
        default="",
        help_text="Result message (e.g., 'Started process step X', 'Blocked: user not certified')"
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional scan metadata as JSON"
    )

    # HTTP request info (for auditing)
    user_agent = models.TextField(
        blank=True,
        default="",
        help_text="Browser/client user agent string"
    )

    session_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Session ID for correlation"
    )

    objects = ScanLogManager()

    class Meta:
        db_table = 'qrcode_scan_log'
        verbose_name = 'Scan Log'
        verbose_name_plural = 'Scan Logs'
        ordering = ['-scan_timestamp']
        indexes = [
            models.Index(fields=['-scan_timestamp'], name='ix_scanlog_timestamp'),
            models.Index(fields=['qcode'], name='ix_scanlog_qcode'),
            models.Index(fields=['scanner_user'], name='ix_scanlog_user'),
            models.Index(fields=['action_type'], name='ix_scanlog_action'),
            models.Index(fields=['success'], name='ix_scanlog_success'),
            models.Index(fields=['scanner_employee_id'], name='ix_scanlog_employee'),
            models.Index(fields=['scanner_location_id'], name='ix_scanlog_location'),
            models.Index(
                fields=['context_content_type', 'context_object_id'],
                name='ix_scanlog_context'
            ),
        ]

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.qcode} at {self.scan_timestamp}"

    @property
    def scanner_display_name(self):
        """Get display name for scanner."""
        if self.scanner_employee_name:
            return self.scanner_employee_name
        if self.scanner_user:
            return str(self.scanner_user)
        return "Anonymous"

    @property
    def location_display(self):
        """Get display string for location."""
        parts = []
        if self.scanner_location_name:
            parts.append(self.scanner_location_name)
        if self.scanner_ip:
            parts.append(f"IP: {self.scanner_ip}")
        if self.scanner_latitude and self.scanner_longitude:
            parts.append(f"GPS: {self.scanner_latitude}, {self.scanner_longitude}")
        return " | ".join(parts) if parts else "Unknown Location"

    @classmethod
    def create_log(cls, qcode, action_type, request=None, user=None,
                   success=True, message="", reason="", context_obj=None,
                   metadata=None):
        """
        Create a scan log entry with common fields populated.

        Args:
            qcode: The QCode that was scanned
            action_type: One of ScanActionType constants
            request: Optional HTTP request object
            user: User who scanned (defaults to request.user)
            success: Whether action succeeded
            message: Result message
            reason: Reason for scan (WHY)
            context_obj: Optional related object
            metadata: Optional dict of additional data

        Returns:
            ScanLog instance
        """
        log = cls(
            qcode=qcode,
            action_type=action_type,
            success=success,
            message=message,
            reason=reason,
            metadata=metadata or {},
        )

        # Extract user info
        if user:
            log.scanner_user = user
        elif request and hasattr(request, 'user') and request.user.is_authenticated:
            log.scanner_user = request.user

        # Try to get employee info
        if log.scanner_user:
            try:
                # Import here to avoid circular import
                from floor_app.operations.hr.models import HREmployee
                employee = HREmployee.objects.filter(user=log.scanner_user).first()
                if employee:
                    log.scanner_employee_id = employee.pk
                    log.scanner_employee_name = str(employee.person) if employee.person else str(employee)
            except Exception:
                pass

        # Extract request info
        if request:
            # IP address
            x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded:
                log.scanner_ip = x_forwarded.split(',')[0].strip()
            else:
                log.scanner_ip = request.META.get('REMOTE_ADDR')

            # User agent
            log.user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Session ID
            if hasattr(request, 'session') and hasattr(request.session, 'session_key'):
                log.session_id = request.session.session_key or ''

            # Device type detection
            if 'Mobile' in log.user_agent:
                log.scanner_device_type = 'MOBILE'
            elif 'API' in request.path or request.content_type == 'application/json':
                log.scanner_device_type = 'API'
            else:
                log.scanner_device_type = 'WEB'

        # Context object
        if context_obj:
            log.context_content_type = ContentType.objects.get_for_model(context_obj)
            log.context_object_id = context_obj.pk

        log.save()

        # Update QCode scan statistics
        qcode.record_scan(user=log.scanner_user)

        return log
