"""
GPS Verification System API Serializers

Serializers for GPS verification system REST API.
"""

from rest_framework import serializers
from floor_app.operations.gps_system.models import (
    LocationVerification,
    Geofence,
    GPSLog
)


class LocationVerificationSerializer(serializers.ModelSerializer):
    """Serializer for location verifications."""

    verification_type_display = serializers.CharField(
        source='get_verification_type_display',
        read_only=True
    )
    verified_by_name = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = LocationVerification
        fields = [
            'id',
            'verification_type',
            'verification_type_display',
            'expected_latitude',
            'expected_longitude',
            'expected_address',
            'geofence_radius_meters',
            'actual_latitude',
            'actual_longitude',
            'actual_address',
            'distance_meters',
            'distance_km',
            'is_within_geofence',
            'verified_at',
            'verified_by',
            'verified_by_name',
            'override_reason',
            'metadata',
            'created_at',
        ]
        read_only_fields = [
            'distance_meters',
            'actual_address',
            'verified_at',
            'created_at',
        ]

    def get_verified_by_name(self, obj):
        """Get verifier's name."""
        if obj.verified_by:
            return obj.verified_by.get_full_name() or obj.verified_by.username
        return None

    def get_distance_km(self, obj):
        """Get distance in kilometers."""
        if obj.distance_meters:
            return round(obj.distance_meters / 1000, 2)
        return None


class LocationVerificationCreateSerializer(serializers.Serializer):
    """Serializer for creating location verifications."""

    verification_type = serializers.ChoiceField(
        choices=[
            'CLOCK_IN', 'CLOCK_OUT', 'DELIVERY', 'PICKUP',
            'INSTALLATION', 'SERVICE', 'INSPECTION', 'CUSTOM'
        ]
    )
    expected_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    expected_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    expected_address = serializers.CharField(max_length=500, required=False)
    geofence_radius_meters = serializers.IntegerField(default=100, min_value=1)
    actual_latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    actual_longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    override_reason = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)


class LocationVerifySerializer(serializers.Serializer):
    """Serializer for verifying a location."""

    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)


class GeofenceSerializer(serializers.ModelSerializer):
    """Serializer for geofences."""

    geofence_type_display = serializers.CharField(
        source='get_geofence_type_display',
        read_only=True
    )
    created_by_name = serializers.SerializerMethodField()
    area_type = serializers.SerializerMethodField()

    class Meta:
        model = Geofence
        fields = [
            'id',
            'name',
            'description',
            'geofence_type',
            'geofence_type_display',
            'area_type',
            'center_latitude',
            'center_longitude',
            'radius_meters',
            'polygon_points',
            'is_active',
            'created_by',
            'created_by_name',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_created_by_name(self, obj):
        """Get creator's name."""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'System'

    def get_area_type(self, obj):
        """Determine if circular or polygon geofence."""
        if obj.center_latitude and obj.center_longitude and obj.radius_meters:
            return 'circular'
        elif obj.polygon_points:
            return 'polygon'
        return 'undefined'


class GeofenceCreateSerializer(serializers.Serializer):
    """Serializer for creating geofences."""

    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    geofence_type = serializers.ChoiceField(
        choices=[
            'WAREHOUSE', 'OFFICE', 'FACTORY', 'STORAGE', 'SITE',
            'DELIVERY_ZONE', 'SERVICE_AREA', 'RESTRICTED', 'CUSTOM'
        ]
    )

    # For circular geofences
    center_latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    center_longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    radius_meters = serializers.IntegerField(required=False, min_value=1)

    # For polygon geofences
    polygon_points = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    is_active = serializers.BooleanField(default=True)
    metadata = serializers.JSONField(required=False)

    def validate(self, data):
        """Validate that either circular or polygon data is provided."""
        has_circular = all([
            data.get('center_latitude'),
            data.get('center_longitude'),
            data.get('radius_meters')
        ])
        has_polygon = data.get('polygon_points') and len(data.get('polygon_points', [])) >= 3

        if not has_circular and not has_polygon:
            raise serializers.ValidationError(
                "Either circular (center_latitude, center_longitude, radius_meters) "
                "or polygon (polygon_points with at least 3 points) data must be provided"
            )

        return data


class GeofenceCheckSerializer(serializers.Serializer):
    """Serializer for checking if point is within geofence."""

    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)


class GPSLogSerializer(serializers.ModelSerializer):
    """Serializer for GPS logs."""

    log_type_display = serializers.CharField(
        source='get_log_type_display',
        read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    distance_from_last = serializers.SerializerMethodField()

    class Meta:
        model = GPSLog
        fields = [
            'id',
            'employee',
            'employee_name',
            'log_type',
            'log_type_display',
            'latitude',
            'longitude',
            'accuracy_meters',
            'altitude_meters',
            'speed_mps',
            'bearing_degrees',
            'address',
            'timestamp',
            'distance_from_last',
            'metadata',
        ]
        read_only_fields = ['timestamp', 'address']

    def get_employee_name(self, obj):
        """Get employee's name."""
        if obj.employee:
            return obj.employee.full_name
        return None

    def get_distance_from_last(self, obj):
        """Get distance from last GPS log."""
        # Get previous log for this employee
        previous_log = GPSLog.objects.filter(
            employee=obj.employee,
            timestamp__lt=obj.timestamp
        ).order_by('-timestamp').first()

        if previous_log:
            from floor_app.operations.gps_system.services import GPSVerificationService
            distance = GPSVerificationService.calculate_distance(
                float(previous_log.latitude),
                float(previous_log.longitude),
                float(obj.latitude),
                float(obj.longitude)
            )
            return round(distance, 2)

        return None


class GPSLogCreateSerializer(serializers.Serializer):
    """Serializer for creating GPS logs."""

    log_type = serializers.ChoiceField(
        choices=[
            'TRACKING', 'CLOCK_IN', 'CLOCK_OUT', 'DELIVERY',
            'PICKUP', 'CHECKPOINT', 'CUSTOM'
        ]
    )
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    accuracy_meters = serializers.FloatField(required=False)
    altitude_meters = serializers.FloatField(required=False)
    speed_mps = serializers.FloatField(required=False)
    bearing_degrees = serializers.FloatField(required=False)
    metadata = serializers.JSONField(required=False)


class DistanceCalculationSerializer(serializers.Serializer):
    """Serializer for calculating distance between two points."""

    lat1 = serializers.DecimalField(max_digits=9, decimal_places=6)
    lon1 = serializers.DecimalField(max_digits=9, decimal_places=6)
    lat2 = serializers.DecimalField(max_digits=9, decimal_places=6)
    lon2 = serializers.DecimalField(max_digits=9, decimal_places=6)


class ReverseGeocodeSerializer(serializers.Serializer):
    """Serializer for reverse geocoding."""

    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
