"""
GPS Location Verification System

Verify that actual GPS location matches expected location with geofencing.

Use Cases:
- Delivery verification (driver at correct address)
- Receiving dock verification (inspector at dock)
- Inventory check verification (employee at physical location)
- Asset tracking (equipment at reported location)
- Employee attendance (at worksite)
- QC checkpoint verification (at correct station)

Features:
- Geofence checking (within radius?)
- Distance calculation
- Reverse geocoding
- GPS accuracy validation
- Override with approval
- History tracking
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import math

from floor_app.mixins import AuditMixin


class LocationVerification(AuditMixin):
    """
    GPS location verification record.

    Compares expected location vs actual GPS location.
    """

    VERIFICATION_TYPES = (
        ('DELIVERY', 'Delivery Confirmation'),
        ('RECEIVING', 'Receiving Dock'),
        ('SHIPPING', 'Shipping Dock'),
        ('INVENTORY_CHECK', 'Inventory Stock Check'),
        ('ASSET_LOCATION', 'Asset Location'),
        ('EMPLOYEE_CHECKIN', 'Employee Check-in'),
        ('QC_CHECKPOINT', 'QC Checkpoint'),
        ('PRODUCTION_STATION', 'Production Station'),
        ('CUSTOM', 'Custom'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified (within geofence)'),
        ('WARNING', 'Warning (outside geofence but close)'),
        ('FAILED', 'Failed (too far)'),
        ('OVERRIDDEN', 'Overridden (manual approval)'),
    )

    # What is being verified
    verification_type = models.CharField(
        max_length=30,
        choices=VERIFICATION_TYPES
    )

    # Linked object (optional - delivery, job card, asset, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    # Expected location (where should be)
    expected_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Expected GPS latitude"
    )
    expected_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Expected GPS longitude"
    )
    expected_address = models.CharField(
        max_length=500,
        blank=True,
        help_text="Expected address"
    )
    geofence_radius_meters = models.PositiveIntegerField(
        default=100,
        help_text="Geofence radius in meters (default 100m)"
    )

    # Actual location (where actually is)
    actual_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Actual GPS latitude"
    )
    actual_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Actual GPS longitude"
    )
    actual_address = models.CharField(
        max_length=500,
        blank=True,
        help_text="Reverse-geocoded actual address"
    )

    # GPS accuracy
    gps_accuracy_meters = models.FloatField(
        null=True,
        blank=True,
        help_text="GPS accuracy in meters (from device)"
    )

    # Verification result
    distance_meters = models.FloatField(
        null=True,
        blank=True,
        help_text="Calculated distance in meters"
    )
    is_within_geofence = models.BooleanField(
        default=False,
        help_text="Is actual location within geofence?"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    # Who verified
    verified_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='location_verifications'
    )
    verified_by_employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='location_verifications'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Device info
    device_info = models.JSONField(
        default=dict,
        help_text="Device information"
    )

    # Override (when location check fails but manually approved)
    override_allowed = models.BooleanField(
        default=True,
        help_text="Can this verification be overridden?"
    )
    is_overridden = models.BooleanField(
        default=False,
        help_text="Was this verification manually overridden?"
    )
    override_reason = models.TextField(
        blank=True,
        help_text="Reason for override"
    )
    overridden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='location_verification_overrides'
    )
    overridden_at = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'gps_location_verification'
        indexes = [
            models.Index(fields=['verification_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-verified_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_verification_type_display()}: {self.status} ({self.distance_meters}m away)"

    def verify_location(
        self,
        actual_lat: Decimal,
        actual_lon: Decimal,
        accuracy: float = None,
        user=None,
        employee=None,
        device_info: dict = None
    ):
        """
        Verify actual GPS location against expected location.

        Args:
            actual_lat: Actual GPS latitude
            actual_lon: Actual GPS longitude
            accuracy: GPS accuracy in meters
            user: User performing verification
            employee: Employee performing verification
            device_info: Device information dict
        """
        from floor_app.operations.gps_system.services import GPSVerificationService

        self.actual_latitude = actual_lat
        self.actual_longitude = actual_lon
        self.gps_accuracy_meters = accuracy
        self.verified_by_user = user
        self.verified_by_employee = employee
        self.verified_at = timezone.now()
        if device_info:
            self.device_info = device_info

        # Calculate distance
        self.distance_meters = GPSVerificationService.calculate_distance(
            float(self.expected_latitude),
            float(self.expected_longitude),
            float(actual_lat),
            float(actual_lon)
        )

        # Check if within geofence
        self.is_within_geofence = self.distance_meters <= self.geofence_radius_meters

        # Determine status
        if self.is_within_geofence:
            self.status = 'VERIFIED'
        elif self.distance_meters <= self.geofence_radius_meters * 2:
            # Within 2x radius: warning
            self.status = 'WARNING'
        else:
            # Too far
            self.status = 'FAILED'

        # Reverse geocode actual location
        try:
            self.actual_address = GPSVerificationService.reverse_geocode(
                float(actual_lat),
                float(actual_lon)
            )
        except:
            pass

        self.save()

    def override(self, reason: str, overridden_by):
        """
        Override a failed verification.

        Args:
            reason: Reason for override
            overridden_by: User who is overriding
        """
        if not self.override_allowed:
            raise ValueError("This verification cannot be overridden")

        self.is_overridden = True
        self.override_reason = reason
        self.overridden_by = overridden_by
        self.overridden_at = timezone.now()
        self.status = 'OVERRIDDEN'
        self.save()


class GeofenceDefinition(models.Model):
    """
    Predefined geofences for common locations.

    E.g., Warehouse, Receiving Dock, Production Floor, etc.
    """

    GEOFENCE_TYPES = (
        ('WAREHOUSE', 'Warehouse'),
        ('RECEIVING_DOCK', 'Receiving Dock'),
        ('SHIPPING_DOCK', 'Shipping Dock'),
        ('PRODUCTION_FLOOR', 'Production Floor'),
        ('QC_LAB', 'QC Laboratory'),
        ('OFFICE', 'Office'),
        ('CUSTOMER_SITE', 'Customer Site'),
        ('CUSTOM', 'Custom Location'),
    )

    GEOFENCE_SHAPES = (
        ('CIRCLE', 'Circle (center + radius)'),
        ('POLYGON', 'Polygon (multiple points)'),
    )

    name = models.CharField(
        max_length=200,
        unique=True
    )
    geofence_type = models.CharField(
        max_length=30,
        choices=GEOFENCE_TYPES
    )
    description = models.TextField(blank=True)

    # Shape
    shape = models.CharField(
        max_length=20,
        choices=GEOFENCE_SHAPES,
        default='CIRCLE'
    )

    # For circle
    center_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    center_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    radius_meters = models.PositiveIntegerField(
        default=100,
        help_text="Geofence radius in meters"
    )

    # For polygon
    polygon_points = models.JSONField(
        default=list,
        help_text="List of lat/lon points for polygon"
    )

    # Address
    address = models.CharField(max_length=500, blank=True)

    # Link to location
    location = models.ForeignKey(
        'inventory.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='geofences'
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'gps_geofence_definition'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_geofence_type_display()})"

    def is_point_inside(self, latitude: float, longitude: float) -> bool:
        """
        Check if a point is inside this geofence.

        Args:
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            True if inside geofence, False otherwise
        """
        from floor_app.operations.gps_system.services import GPSVerificationService

        if self.shape == 'CIRCLE':
            distance = GPSVerificationService.calculate_distance(
                float(self.center_latitude),
                float(self.center_longitude),
                latitude,
                longitude
            )
            return distance <= self.radius_meters
        elif self.shape == 'POLYGON':
            return GPSVerificationService.is_point_in_polygon(
                latitude,
                longitude,
                self.polygon_points
            )

        return False


class GPSTrackingLog(models.Model):
    """
    Continuous GPS tracking log.

    For tracking employee/asset movement over time.
    """

    # Who/what is being tracked
    tracked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='gps_tracking_logs'
    )
    tracked_employee = models.ForeignKey(
        'hr.HREmployee',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='gps_tracking_logs'
    )

    # Tracked object (e.g., delivery vehicle, equipment)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    tracked_object = GenericForeignKey('content_type', 'object_id')

    # GPS location
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )
    accuracy_meters = models.FloatField(null=True, blank=True)

    # Altitude (optional)
    altitude_meters = models.FloatField(null=True, blank=True)

    # Speed (optional)
    speed_mps = models.FloatField(
        null=True,
        blank=True,
        help_text="Speed in meters per second"
    )
    heading_degrees = models.FloatField(
        null=True,
        blank=True,
        help_text="Heading in degrees (0-360)"
    )

    # Timestamp
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Device
    device_info = models.JSONField(default=dict)

    # Reverse geocoded address (optional, expensive)
    address = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'gps_tracking_log'
        indexes = [
            models.Index(fields=['tracked_user', '-recorded_at']),
            models.Index(fields=['tracked_employee', '-recorded_at']),
            models.Index(fields=['content_type', 'object_id', '-recorded_at']),
            models.Index(fields=['-recorded_at']),
        ]
        ordering = ['-recorded_at']

    def __str__(self):
        tracker = self.tracked_user or self.tracked_employee or 'Unknown'
        return f"{tracker} at ({self.latitude}, {self.longitude}) on {self.recorded_at}"
