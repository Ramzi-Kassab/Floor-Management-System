"""
Device Tracking API Views

REST API viewsets for device tracking system.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta

from floor_app.operations.device_tracking.models import (
    EmployeeDevice,
    EmployeeActivity,
    EmployeePresence,
    DeviceSession,
    DeviceNotificationPreference
)
from floor_app.operations.device_tracking.services import DeviceTrackingService
from .serializers import (
    EmployeeDeviceSerializer,
    EmployeeDeviceRegisterSerializer,
    EmployeeActivitySerializer,
    EmployeeActivityCreateSerializer,
    EmployeePresenceSerializer,
    ClockInOutSerializer,
    DeviceSessionSerializer,
    DeviceNotificationPreferenceSerializer
)


class EmployeeDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employee devices.

    list: Get all employee devices
    retrieve: Get a specific device
    create: Register a new device
    update: Update device information
    destroy: Deactivate a device
    """

    serializer_class = EmployeeDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['device_type', 'is_active', 'is_primary_device', 'employee']
    search_fields = ['device_name', 'device_id', 'device_model']
    ordering = ['-is_primary_device', '-last_seen_at']

    def get_queryset(self):
        """Users can only see their own devices, admins see all."""
        user = self.request.user

        if user.is_staff:
            return EmployeeDevice.objects.all().select_related('employee', 'user')

        # Regular users see their own devices
        try:
            employee = user.hremployee
            return EmployeeDevice.objects.filter(
                Q(user=user) | Q(employee=employee)
            ).select_related('employee', 'user')
        except Exception:
            return EmployeeDevice.objects.filter(user=user).select_related('employee', 'user')

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'register':
            return EmployeeDeviceRegisterSerializer
        return EmployeeDeviceSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register a new device for current user.

        POST /api/devices/register/
        Body: {
            "device_id": "abc123-xyz789",
            "device_type": "ANDROID",
            "device_name": "My Phone",
            "device_model": "Samsung Galaxy S21",
            "os_version": "Android 12",
            "app_version": "1.0.0",
            "fcm_token": "fcm_token_here"
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get employee for current user
        try:
            employee = request.user.hremployee
        except Exception:
            return Response(
                {'error': 'User does not have an associated employee record'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Register device
        device = DeviceTrackingService.register_device(
            employee=employee,
            device_id=data['device_id'],
            device_type=data['device_type'],
            device_name=data.get('device_name', ''),
            device_model=data.get('device_model', ''),
            os_version=data.get('os_version', ''),
            app_version=data.get('app_version', ''),
            fcm_token=data.get('fcm_token', ''),
            metadata=data.get('metadata', {})
        )

        output_serializer = EmployeeDeviceSerializer(device, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def make_primary(self, request, pk=None):
        """
        Make this device the primary device.

        POST /api/devices/{id}/make_primary/
        """
        device = self.get_object()

        # Check ownership
        if not (request.user.is_staff or
                (hasattr(device, 'employee') and device.employee.user == request.user)):
            return Response(
                {'error': 'You do not have permission to modify this device'},
                status=status.HTTP_403_FORBIDDEN
            )

        device.make_primary()

        serializer = self.get_serializer(device, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_fcm_token(self, request, pk=None):
        """
        Update FCM token for push notifications.

        POST /api/devices/{id}/update_fcm_token/
        Body: {
            "fcm_token": "new_fcm_token_here"
        }
        """
        device = self.get_object()

        # Check ownership
        if not (request.user.is_staff or
                (hasattr(device, 'employee') and device.employee.user == request.user)):
            return Response(
                {'error': 'You do not have permission to modify this device'},
                status=status.HTTP_403_FORBIDDEN
            )

        fcm_token = request.data.get('fcm_token')
        if not fcm_token:
            return Response(
                {'error': 'fcm_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        DeviceTrackingService.update_fcm_token(device.device_id, fcm_token)

        serializer = self.get_serializer(device, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a device.

        POST /api/devices/{id}/deactivate/
        Body: {
            "reason": "Device lost/stolen"
        }
        """
        device = self.get_object()

        # Check ownership or admin
        if not (request.user.is_staff or
                (hasattr(device, 'employee') and device.employee.user == request.user)):
            return Response(
                {'error': 'You do not have permission to deactivate this device'},
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get('reason', 'Deactivated by user')
        DeviceTrackingService.deactivate_device(
            device.device_id,
            reason=reason,
            deactivated_by=request.user
        )

        serializer = self.get_serializer(device, context={'request': request})
        return Response(serializer.data)


class EmployeeActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employee activities.

    list: Get all activities
    retrieve: Get a specific activity
    create: Log a new activity
    """

    serializer_class = EmployeeActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['activity_type', 'employee', 'device']
    ordering = ['-activity_at']

    def get_queryset(self):
        """Users see their own activities, admins see all."""
        user = self.request.user

        if user.is_staff:
            return EmployeeActivity.objects.all().select_related('employee', 'device')

        try:
            employee = user.hremployee
            return EmployeeActivity.objects.filter(employee=employee).select_related('employee', 'device')
        except Exception:
            return EmployeeActivity.objects.none()

    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return EmployeeActivityCreateSerializer
        return EmployeeActivitySerializer

    def create(self, request, *args, **kwargs):
        """
        Log a new activity.

        POST /api/employee-activities/
        Body: {
            "activity_type": "SCAN_QR",
            "description": "Scanned cutter QR code",
            "latitude": 24.1234,
            "longitude": 55.5678,
            "accuracy": 5.2,
            "metadata": {"qr_code": "QR-001"}
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get employee and device
        try:
            employee = request.user.hremployee
            device = employee.devices.filter(is_active=True, is_primary_device=True).first()

            if not device:
                device = employee.devices.filter(is_active=True).first()

            if not device:
                return Response(
                    {'error': 'No active device found for this employee'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception:
            return Response(
                {'error': 'User does not have an associated employee record'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Log activity
        activity = DeviceTrackingService.log_activity(
            employee=employee,
            device=device,
            activity_type=data['activity_type'],
            description=data.get('description', ''),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            accuracy=data.get('accuracy'),
            metadata=data.get('metadata', {})
        )

        output_serializer = EmployeeActivitySerializer(activity)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent activities (last 24 hours).

        GET /api/employee-activities/recent/
        """
        since = timezone.now() - timedelta(hours=24)
        queryset = self.get_queryset().filter(activity_at__gte=since)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class EmployeePresenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employee presence/attendance.

    list: Get all presence records
    retrieve: Get a specific presence record
    """

    serializer_class = EmployeePresenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'date', 'employee', 'is_verified']
    ordering = ['-date']

    def get_queryset(self):
        """Users see their own presence, admins see all."""
        user = self.request.user

        if user.is_staff:
            return EmployeePresence.objects.all().select_related(
                'employee', 'clock_in_device', 'clock_out_device'
            )

        try:
            employee = user.hremployee
            return EmployeePresence.objects.filter(employee=employee).select_related(
                'employee', 'clock_in_device', 'clock_out_device'
            )
        except Exception:
            return EmployeePresence.objects.none()

    @action(detail=False, methods=['post'])
    def clock_in(self, request):
        """
        Clock in for today.

        POST /api/employee-presence/clock_in/
        Body: {
            "latitude": 24.1234,
            "longitude": 55.5678
        }
        """
        serializer = ClockInOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get employee and device
        try:
            employee = request.user.hremployee
            device = employee.devices.filter(is_active=True, is_primary_device=True).first()

            if not device:
                device = employee.devices.filter(is_active=True).first()

            if not device:
                return Response(
                    {'error': 'No active device found'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception:
            return Response(
                {'error': 'User does not have an associated employee record'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Clock in
        presence = DeviceTrackingService.clock_in(
            employee=employee,
            device=device,
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )

        output_serializer = self.get_serializer(presence)
        return Response(output_serializer.data)

    @action(detail=False, methods=['post'])
    def clock_out(self, request):
        """
        Clock out for today.

        POST /api/employee-presence/clock_out/
        Body: {
            "latitude": 24.1234,
            "longitude": 55.5678
        }
        """
        serializer = ClockInOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Get employee and device
        try:
            employee = request.user.hremployee
            device = employee.devices.filter(is_active=True, is_primary_device=True).first()

            if not device:
                device = employee.devices.filter(is_active=True).first()

            if not device:
                return Response(
                    {'error': 'No active device found'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception:
            return Response(
                {'error': 'User does not have an associated employee record'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Clock out
        presence = DeviceTrackingService.clock_out(
            employee=employee,
            device=device,
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )

        if not presence:
            return Response(
                {'error': 'No clock-in record found for today'},
                status=status.HTTP_400_BAD_REQUEST
            )

        output_serializer = self.get_serializer(presence)
        return Response(output_serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get presence record for today.

        GET /api/employee-presence/today/
        """
        try:
            employee = request.user.hremployee
            presence = DeviceTrackingService.get_employee_presence_today(employee)

            if not presence:
                return Response({
                    'message': 'No presence record for today',
                    'is_clocked_in': False
                })

            serializer = self.get_serializer(presence)
            return Response(serializer.data)

        except Exception:
            return Response(
                {'error': 'User does not have an associated employee record'},
                status=status.HTTP_400_BAD_REQUEST
            )


class DeviceSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing device sessions (read-only).

    list: Get all sessions
    retrieve: Get a specific session
    """

    serializer_class = DeviceSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['device', 'employee', 'is_active']
    ordering = ['-started_at']

    def get_queryset(self):
        """Users see their own sessions, admins see all."""
        user = self.request.user

        if user.is_staff:
            return DeviceSession.objects.all().select_related('device', 'employee')

        try:
            employee = user.hremployee
            return DeviceSession.objects.filter(employee=employee).select_related('device', 'employee')
        except Exception:
            return DeviceSession.objects.none()

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get active sessions for current user.

        GET /api/device-sessions/active/
        """
        queryset = self.get_queryset().filter(is_active=True)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
