"""
Device Tracking API Serializers

Serializers for device tracking system REST API.
"""

from rest_framework import serializers
from floor_app.operations.device_tracking.models import (
    EmployeeDevice,
    EmployeeActivity,
    EmployeePresence,
    DeviceSession,
    DeviceNotificationPreference
)


class EmployeeDeviceSerializer(serializers.ModelSerializer):
    """Serializer for employee devices."""

    device_type_display = serializers.CharField(
        source='get_device_type_display',
        read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    is_online = serializers.BooleanField(read_only=True)

    class Meta:
        model = EmployeeDevice
        fields = [
            'id',
            'employee',
            'employee_name',
            'user',
            'device_id',
            'device_name',
            'device_type',
            'device_type_display',
            'device_model',
            'os_version',
            'app_version',
            'registered_at',
            'last_seen_at',
            'is_primary_device',
            'is_trusted',
            'is_active',
            'is_online',
            'fcm_token',
            'push_enabled',
            'metadata',
        ]
        read_only_fields = ['registered_at', 'last_seen_at', 'is_online']

    def get_employee_name(self, obj):
        """Get employee's name."""
        if obj.employee:
            return obj.employee.full_name
        return None

    def to_representation(self, instance):
        """Hide FCM token from non-admin users."""
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request and request.user:
            # Only show FCM token to device owner or admin
            if not (request.user.is_staff or
                    (hasattr(instance, 'employee') and
                     instance.employee.user == request.user)):
                data.pop('fcm_token', None)

        return data


class EmployeeDeviceRegisterSerializer(serializers.Serializer):
    """Serializer for registering a new device."""

    device_id = serializers.CharField(max_length=255)
    device_type = serializers.ChoiceField(
        choices=['ANDROID', 'IOS', 'WEB', 'DESKTOP']
    )
    device_name = serializers.CharField(max_length=200, required=False)
    device_model = serializers.CharField(max_length=100, required=False)
    os_version = serializers.CharField(max_length=50, required=False)
    app_version = serializers.CharField(max_length=50, required=False)
    fcm_token = serializers.CharField(max_length=255, required=False)
    metadata = serializers.JSONField(required=False)


class EmployeeActivitySerializer(serializers.ModelSerializer):
    """Serializer for employee activities."""

    activity_type_display = serializers.CharField(
        source='get_activity_type_display',
        read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    device_name = serializers.CharField(source='device.device_name', read_only=True)

    class Meta:
        model = EmployeeActivity
        fields = [
            'id',
            'employee',
            'employee_name',
            'device',
            'device_name',
            'activity_type',
            'activity_type_display',
            'activity_description',
            'activity_at',
            'latitude',
            'longitude',
            'gps_accuracy_meters',
            'metadata',
        ]
        read_only_fields = ['activity_at']

    def get_employee_name(self, obj):
        """Get employee's name."""
        if obj.employee:
            return obj.employee.full_name
        return None


class EmployeeActivityCreateSerializer(serializers.Serializer):
    """Serializer for logging employee activities."""

    activity_type = serializers.ChoiceField(
        choices=[
            'LOGIN', 'LOGOUT', 'CLOCK_IN', 'CLOCK_OUT', 'SCAN_QR',
            'GPS_CHECK', 'NOTIFICATION_READ', 'APPROVAL_ACTION',
            'MAP_UPDATE', 'INVENTORY_ACTION', 'JOB_CARD_VIEW',
            'PHOTO_CAPTURE', 'CUSTOM'
        ]
    )
    description = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    accuracy = serializers.FloatField(required=False)
    metadata = serializers.JSONField(required=False)


class EmployeePresenceSerializer(serializers.ModelSerializer):
    """Serializer for employee presence/attendance."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    is_clocked_in = serializers.BooleanField(read_only=True)
    clock_in_device_name = serializers.CharField(
        source='clock_in_device.device_name',
        read_only=True
    )
    clock_out_device_name = serializers.CharField(
        source='clock_out_device.device_name',
        read_only=True
    )

    class Meta:
        model = EmployeePresence
        fields = [
            'id',
            'employee',
            'employee_name',
            'date',
            'clock_in_time',
            'clock_in_latitude',
            'clock_in_longitude',
            'clock_in_device',
            'clock_in_device_name',
            'clock_out_time',
            'clock_out_latitude',
            'clock_out_longitude',
            'clock_out_device',
            'clock_out_device_name',
            'total_hours',
            'status',
            'status_display',
            'is_verified',
            'verified_by',
            'verified_at',
            'notes',
            'is_clocked_in',
        ]
        read_only_fields = [
            'clock_in_time',
            'clock_out_time',
            'total_hours',
            'verified_at',
        ]

    def get_employee_name(self, obj):
        """Get employee's name."""
        if obj.employee:
            return obj.employee.full_name
        return None


class ClockInOutSerializer(serializers.Serializer):
    """Serializer for clock in/out actions."""

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )


class DeviceSessionSerializer(serializers.ModelSerializer):
    """Serializer for device sessions."""

    employee_name = serializers.SerializerMethodField()
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    duration_minutes = serializers.FloatField(read_only=True)

    class Meta:
        model = DeviceSession
        fields = [
            'id',
            'device',
            'device_name',
            'employee',
            'employee_name',
            'session_token',
            'started_at',
            'ended_at',
            'last_activity_at',
            'duration_minutes',
            'start_latitude',
            'start_longitude',
            'ip_address',
            'user_agent',
            'is_active',
        ]
        read_only_fields = [
            'session_token',
            'started_at',
            'ended_at',
            'last_activity_at',
        ]

    def get_employee_name(self, obj):
        """Get employee's name."""
        if obj.employee:
            return obj.employee.full_name
        return None

    def to_representation(self, instance):
        """Hide session token from non-admin users."""
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request and request.user:
            # Only show session token to session owner or admin
            if not (request.user.is_staff or
                    (hasattr(instance, 'employee') and
                     instance.employee.user == request.user)):
                data.pop('session_token', None)

        return data


class DeviceNotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for device notification preferences."""

    device_name = serializers.CharField(source='device.device_name', read_only=True)

    class Meta:
        model = DeviceNotificationPreference
        fields = [
            'id',
            'device',
            'device_name',
            'enable_approval_notifications',
            'enable_job_notifications',
            'enable_inventory_notifications',
            'enable_qc_notifications',
            'enable_system_notifications',
            'enable_sound',
            'enable_vibration',
            'quiet_hours_enabled',
            'quiet_hours_start',
            'quiet_hours_end',
        ]
