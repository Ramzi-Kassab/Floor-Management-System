"""
Employee Device Tracking System

Track employees by their phone/device IDs for:
- Auto-login and identification
- Attendance tracking (clock in/out)
- Location tracking
- Activity logging
- Push notification targeting
- Security (only registered devices)

Features:
- Device registration and management
- Activity logging
- Presence/attendance tracking
- Multi-device support per employee
- Trusted device management
- Security controls
"""

from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

from floor_app.mixins import AuditMixin


class EmployeeDevice(AuditMixin):
    """
    Employee's registered device.

    Links employee to their phone/tablet/computer.
    """

    DEVICE_TYPES = (
        ('ANDROID', 'Android Phone/Tablet'),
        ('IOS', 'iOS (iPhone/iPad)'),
        ('WEB', 'Web Browser'),
        ('DESKTOP', 'Desktop Application'),
    )

    # Employee
    employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        related_name='devices'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='devices',
        null=True,
        blank=True
    )

    # Device identification
    device_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique device identifier (IMEI, UUID, etc.)"
    )
    device_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="User-friendly device name (e.g., 'Ahmed's iPhone')"
    )
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPES
    )

    # Device info
    device_model = models.CharField(
        max_length=100,
        blank=True,
        help_text="Device model (e.g., 'iPhone 13 Pro', 'Samsung Galaxy S21')"
    )
    os_version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Operating system version"
    )
    app_version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Mobile app version"
    )

    # Registration
    registered_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time device was seen (auto-updated)"
    )

    # Status
    is_primary_device = models.BooleanField(
        default=False,
        help_text="Is this the employee's primary device?"
    )
    is_trusted = models.BooleanField(
        default=False,
        help_text="Is this device trusted for sensitive operations?"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this device currently active?"
    )

    # Push notifications
    fcm_token = models.CharField(
        max_length=255,
        blank=True,
        help_text="Firebase Cloud Messaging token for push notifications"
    )
    push_enabled = models.BooleanField(
        default=True,
        help_text="Are push notifications enabled on this device?"
    )

    # Security
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.TextField(blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deactivated_devices'
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional device metadata"
    )

    class Meta:
        db_table = 'device_tracking_employee_device'
        indexes = [
            models.Index(fields=['employee', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['-last_seen_at']),
            models.Index(fields=['is_primary_device', 'is_active']),
        ]
        ordering = ['-is_primary_device', '-last_seen_at']

    def __str__(self):
        return f"{self.employee} - {self.device_name or self.device_id}"

    def update_last_seen(self):
        """Update last seen timestamp."""
        self.last_seen_at = timezone.now()
        self.save(update_fields=['last_seen_at'])

    def deactivate(self, reason: str = '', deactivated_by=None):
        """Deactivate this device."""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.deactivation_reason = reason
        self.deactivated_by = deactivated_by
        self.save()

    def make_primary(self):
        """Make this device the primary device for this employee."""
        # Unset other primary devices
        EmployeeDevice.objects.filter(
            employee=self.employee,
            is_primary_device=True
        ).exclude(id=self.id).update(is_primary_device=False)

        self.is_primary_device = True
        self.save(update_fields=['is_primary_device'])

    @property
    def is_online(self):
        """Check if device is currently online (seen in last 5 minutes)."""
        if not self.last_seen_at:
            return False

        time_diff = timezone.now() - self.last_seen_at
        return time_diff.total_seconds() < 300  # 5 minutes


class EmployeeActivity(models.Model):
    """
    Log employee activity from devices.

    Tracks what employees are doing in the system.
    """

    ACTIVITY_TYPES = (
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('CLOCK_IN', 'Clock In'),
        ('CLOCK_OUT', 'Clock Out'),
        ('SCAN_QR', 'QR Code Scan'),
        ('GPS_CHECK', 'GPS Location Check'),
        ('NOTIFICATION_READ', 'Notification Read'),
        ('APPROVAL_ACTION', 'Approval Action'),
        ('MAP_UPDATE', 'Map Update'),
        ('INVENTORY_ACTION', 'Inventory Action'),
        ('JOB_CARD_VIEW', 'Job Card View'),
        ('PHOTO_CAPTURE', 'Photo Capture'),
        ('CUSTOM', 'Custom Activity'),
    )

    # Who
    employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        related_name='activities'
    )
    device = models.ForeignKey(
        EmployeeDevice,
        on_delete=models.CASCADE,
        related_name='activities'
    )

    # What
    activity_type = models.CharField(
        max_length=30,
        choices=ACTIVITY_TYPES,
        db_index=True
    )
    activity_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Human-readable description of activity"
    )

    # When
    activity_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Where (GPS location at time of activity)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    gps_accuracy_meters = models.FloatField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional activity metadata"
    )

    class Meta:
        db_table = 'device_tracking_employee_activity'
        verbose_name_plural = 'Employee activities'
        indexes = [
            models.Index(fields=['employee', '-activity_at']),
            models.Index(fields=['device', '-activity_at']),
            models.Index(fields=['activity_type', '-activity_at']),
            models.Index(fields=['-activity_at']),
        ]
        ordering = ['-activity_at']

    def __str__(self):
        return f"{self.employee} - {self.get_activity_type_display()} at {self.activity_at}"


class EmployeePresence(models.Model):
    """
    Employee presence/attendance tracking.

    One record per employee per day.
    """

    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('LEFT_EARLY', 'Left Early'),
        ('ON_LEAVE', 'On Leave'),
        ('OFF_DAY', 'Off Day'),
    )

    employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        related_name='presence_records'
    )
    date = models.DateField(db_index=True)

    # Clock in
    clock_in_time = models.DateTimeField(
        null=True,
        blank=True
    )
    clock_in_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    clock_in_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    clock_in_device = models.ForeignKey(
        EmployeeDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clock_ins'
    )

    # Clock out
    clock_out_time = models.DateTimeField(
        null=True,
        blank=True
    )
    clock_out_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    clock_out_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    clock_out_device = models.ForeignKey(
        EmployeeDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clock_outs'
    )

    # Calculated
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total hours worked"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PRESENT'
    )

    # Verification
    is_verified = models.BooleanField(
        default=False,
        help_text="Has presence been verified by supervisor?"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_presence_records'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'device_tracking_employee_presence'
        unique_together = [('employee', 'date')]
        indexes = [
            models.Index(fields=['employee', '-date']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['is_verified']),
        ]
        ordering = ['-date', 'employee']

    def __str__(self):
        return f"{self.employee} on {self.date}: {self.status}"

    def clock_in(self, device, latitude=None, longitude=None):
        """Record clock in."""
        self.clock_in_time = timezone.now()
        self.clock_in_device = device
        self.clock_in_latitude = latitude
        self.clock_in_longitude = longitude
        self.status = 'PRESENT'
        self.save()

    def clock_out(self, device, latitude=None, longitude=None):
        """Record clock out and calculate total hours."""
        self.clock_out_time = timezone.now()
        self.clock_out_device = device
        self.clock_out_latitude = latitude
        self.clock_out_longitude = longitude

        # Calculate total hours
        if self.clock_in_time:
            time_diff = self.clock_out_time - self.clock_in_time
            self.total_hours = Decimal(time_diff.total_seconds() / 3600)

        self.save()

    @property
    def is_clocked_in(self):
        """Check if currently clocked in."""
        return self.clock_in_time is not None and self.clock_out_time is None


class DeviceSession(models.Model):
    """
    Device session tracking.

    One record per login session.
    """

    device = models.ForeignKey(
        EmployeeDevice,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        related_name='device_sessions'
    )

    # Session info
    session_token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Session token (JWT or similar)"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    # GPS at session start
    start_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    start_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    # Session metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'device_tracking_session'
        indexes = [
            models.Index(fields=['device', 'is_active']),
            models.Index(fields=['employee', 'is_active']),
            models.Index(fields=['-started_at']),
        ]
        ordering = ['-started_at']

    def __str__(self):
        return f"Session for {self.employee} started {self.started_at}"

    def end_session(self):
        """End this session."""
        self.ended_at = timezone.now()
        self.is_active = False
        self.save()

    @property
    def duration_minutes(self):
        """Get session duration in minutes."""
        if not self.ended_at:
            # Still active
            duration = timezone.now() - self.started_at
        else:
            duration = self.ended_at - self.started_at

        return duration.total_seconds() / 60


class DeviceNotificationPreference(models.Model):
    """
    Per-device notification preferences.

    Allows different notification settings per device.
    """

    device = models.OneToOneField(
        EmployeeDevice,
        on_delete=models.CASCADE,
        related_name='notification_preference'
    )

    # Notification types
    enable_approval_notifications = models.BooleanField(default=True)
    enable_job_notifications = models.BooleanField(default=True)
    enable_inventory_notifications = models.BooleanField(default=True)
    enable_qc_notifications = models.BooleanField(default=True)
    enable_system_notifications = models.BooleanField(default=True)

    # Sound/vibration
    enable_sound = models.BooleanField(default=True)
    enable_vibration = models.BooleanField(default=True)

    # Quiet hours (per device)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'device_tracking_notification_preference'

    def __str__(self):
        return f"Notification preferences for {self.device}"
