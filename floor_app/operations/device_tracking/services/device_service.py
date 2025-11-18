"""
Device Tracking Service

Manage employee devices, track activity, handle presence.
"""

from django.utils import timezone
from typing import Optional, Dict, Any
import uuid


class DeviceTrackingService:
    """
    Main service for device tracking operations.
    """

    @classmethod
    def register_device(
        cls,
        employee,
        device_id: str,
        device_type: str,
        device_name: str = '',
        device_model: str = '',
        os_version: str = '',
        app_version: str = '',
        fcm_token: str = '',
        metadata: Dict = None
    ):
        """
        Register a new device for an employee.

        Args:
            employee: HREmployee instance
            device_id: Unique device identifier
            device_type: Device type (ANDROID, IOS, WEB, DESKTOP)
            device_name: User-friendly device name
            device_model: Device model
            os_version: OS version
            app_version: App version
            fcm_token: FCM token for push notifications
            metadata: Additional metadata

        Returns:
            EmployeeDevice instance

        Example:
            device = DeviceTrackingService.register_device(
                employee=employee,
                device_id='abc123-xyz789',
                device_type='ANDROID',
                device_name="Ahmed's Phone",
                device_model='Samsung Galaxy S21',
                os_version='Android 12',
                app_version='1.0.0',
                fcm_token='fcm_token_here'
            )
        """
        from floor_app.operations.device_tracking.models import EmployeeDevice

        # Check if device already exists
        existing_device = EmployeeDevice.objects.filter(device_id=device_id).first()
        if existing_device:
            # Update existing device
            existing_device.employee = employee
            existing_device.device_name = device_name or existing_device.device_name
            existing_device.device_model = device_model or existing_device.device_model
            existing_device.os_version = os_version or existing_device.os_version
            existing_device.app_version = app_version or existing_device.app_version
            existing_device.fcm_token = fcm_token or existing_device.fcm_token
            if metadata:
                existing_device.metadata.update(metadata)
            existing_device.is_active = True
            existing_device.save()
            return existing_device

        # Create new device
        device = EmployeeDevice.objects.create(
            employee=employee,
            user=employee.user if hasattr(employee, 'user') else None,
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            device_model=device_model,
            os_version=os_version,
            app_version=app_version,
            fcm_token=fcm_token,
            metadata=metadata or {},
            is_trusted=False,  # Must be manually trusted
        )

        # If this is the first device, make it primary
        if employee.devices.count() == 1:
            device.make_primary()

        return device

    @classmethod
    def get_employee_by_device(cls, device_id: str):
        """
        Get employee by device ID.

        Args:
            device_id: Unique device identifier

        Returns:
            HREmployee instance or None

        Example:
            employee = DeviceTrackingService.get_employee_by_device('abc123')
        """
        from floor_app.operations.device_tracking.models import EmployeeDevice

        try:
            device = EmployeeDevice.objects.select_related('employee').get(
                device_id=device_id,
                is_active=True
            )
            return device.employee
        except EmployeeDevice.DoesNotExist:
            return None

    @classmethod
    def verify_device(cls, device_id: str) -> bool:
        """
        Verify if device is registered and active.

        Args:
            device_id: Device ID to verify

        Returns:
            True if valid, False otherwise
        """
        from floor_app.operations.device_tracking.models import EmployeeDevice

        return EmployeeDevice.objects.filter(
            device_id=device_id,
            is_active=True
        ).exists()

    @classmethod
    def log_activity(
        cls,
        employee,
        device,
        activity_type: str,
        description: str = '',
        latitude: float = None,
        longitude: float = None,
        accuracy: float = None,
        metadata: Dict = None
    ):
        """
        Log employee activity.

        Args:
            employee: HREmployee instance
            device: EmployeeDevice instance
            activity_type: Activity type (from EmployeeActivity.ACTIVITY_TYPES)
            description: Activity description
            latitude: GPS latitude
            longitude: GPS longitude
            accuracy: GPS accuracy
            metadata: Additional metadata

        Returns:
            EmployeeActivity instance

        Example:
            activity = DeviceTrackingService.log_activity(
                employee=employee,
                device=device,
                activity_type='SCAN_QR',
                description='Scanned cutter QR code QR-001',
                latitude=24.1234,
                longitude=55.5678,
                metadata={'qr_code': 'QR-001', 'cutter_id': 123}
            )
        """
        from floor_app.operations.device_tracking.models import EmployeeActivity

        activity = EmployeeActivity.objects.create(
            employee=employee,
            device=device,
            activity_type=activity_type,
            activity_description=description,
            latitude=latitude,
            longitude=longitude,
            gps_accuracy_meters=accuracy,
            metadata=metadata or {}
        )

        # Update device last seen
        device.update_last_seen()

        return activity

    @classmethod
    def clock_in(
        cls,
        employee,
        device,
        latitude: float = None,
        longitude: float = None
    ):
        """
        Clock in employee.

        Args:
            employee: HREmployee instance
            device: EmployeeDevice instance
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            EmployeePresence instance

        Example:
            presence = DeviceTrackingService.clock_in(
                employee=employee,
                device=device,
                latitude=24.1234,
                longitude=55.5678
            )
        """
        from floor_app.operations.device_tracking.models import EmployeePresence

        today = timezone.now().date()

        # Get or create presence record
        presence, created = EmployeePresence.objects.get_or_create(
            employee=employee,
            date=today
        )

        # Clock in
        presence.clock_in(device, latitude, longitude)

        # Log activity
        cls.log_activity(
            employee=employee,
            device=device,
            activity_type='CLOCK_IN',
            description=f'Clocked in at {timezone.now().strftime("%H:%M")}',
            latitude=latitude,
            longitude=longitude
        )

        return presence

    @classmethod
    def clock_out(
        cls,
        employee,
        device,
        latitude: float = None,
        longitude: float = None
    ):
        """
        Clock out employee.

        Args:
            employee: HREmployee instance
            device: EmployeeDevice instance
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            EmployeePresence instance

        Example:
            presence = DeviceTrackingService.clock_out(
                employee=employee,
                device=device,
                latitude=24.1234,
                longitude=55.5678
            )
        """
        from floor_app.operations.device_tracking.models import EmployeePresence

        today = timezone.now().date()

        try:
            presence = EmployeePresence.objects.get(
                employee=employee,
                date=today
            )

            # Clock out
            presence.clock_out(device, latitude, longitude)

            # Log activity
            cls.log_activity(
                employee=employee,
                device=device,
                activity_type='CLOCK_OUT',
                description=f'Clocked out at {timezone.now().strftime("%H:%M")}',
                latitude=latitude,
                longitude=longitude
            )

            return presence

        except EmployeePresence.DoesNotExist:
            # No clock-in record
            return None

    @classmethod
    def get_active_devices(cls, employee):
        """
        Get all active devices for an employee.

        Args:
            employee: HREmployee instance

        Returns:
            QuerySet of EmployeeDevice
        """
        from floor_app.operations.device_tracking.models import EmployeeDevice

        return EmployeeDevice.objects.filter(
            employee=employee,
            is_active=True
        )

    @classmethod
    def deactivate_device(cls, device_id: str, reason: str = '', deactivated_by=None):
        """
        Deactivate a device.

        Args:
            device_id: Device ID to deactivate
            reason: Reason for deactivation
            deactivated_by: User who deactivated

        Returns:
            Boolean indicating success
        """
        from floor_app.operations.device_tracking.models import EmployeeDevice

        try:
            device = EmployeeDevice.objects.get(device_id=device_id)
            device.deactivate(reason, deactivated_by)
            return True
        except EmployeeDevice.DoesNotExist:
            return False

    @classmethod
    def create_session(
        cls,
        device,
        employee,
        latitude: float = None,
        longitude: float = None,
        ip_address: str = '',
        user_agent: str = ''
    ):
        """
        Create a new device session.

        Args:
            device: EmployeeDevice instance
            employee: HREmployee instance
            latitude: GPS latitude at session start
            longitude: GPS longitude at session start
            ip_address: IP address
            user_agent: User agent string

        Returns:
            DeviceSession instance

        Example:
            session = DeviceTrackingService.create_session(
                device=device,
                employee=employee,
                latitude=24.1234,
                longitude=55.5678,
                ip_address='192.168.1.100',
                user_agent='FloorApp/1.0.0 (Android 12)'
            )
        """
        from floor_app.operations.device_tracking.models import DeviceSession
        import secrets

        # Generate session token
        session_token = secrets.token_urlsafe(32)

        session = DeviceSession.objects.create(
            device=device,
            employee=employee,
            session_token=session_token,
            start_latitude=latitude,
            start_longitude=longitude,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Log activity
        cls.log_activity(
            employee=employee,
            device=device,
            activity_type='LOGIN',
            description='User logged in',
            latitude=latitude,
            longitude=longitude
        )

        return session

    @classmethod
    def end_session(cls, session_token: str):
        """
        End a device session.

        Args:
            session_token: Session token

        Returns:
            Boolean indicating success
        """
        from floor_app.operations.device_tracking.models import DeviceSession

        try:
            session = DeviceSession.objects.get(session_token=session_token, is_active=True)
            session.end_session()

            # Log activity
            cls.log_activity(
                employee=session.employee,
                device=session.device,
                activity_type='LOGOUT',
                description='User logged out'
            )

            return True
        except DeviceSession.DoesNotExist:
            return False

    @classmethod
    def get_employee_presence_today(cls, employee):
        """
        Get employee's presence record for today.

        Args:
            employee: HREmployee instance

        Returns:
            EmployeePresence instance or None
        """
        from floor_app.operations.device_tracking.models import EmployeePresence

        today = timezone.now().date()

        return EmployeePresence.objects.filter(
            employee=employee,
            date=today
        ).first()

    @classmethod
    def update_fcm_token(cls, device_id: str, fcm_token: str):
        """
        Update FCM token for a device.

        Args:
            device_id: Device ID
            fcm_token: New FCM token

        Returns:
            Boolean indicating success
        """
        from floor_app.operations.device_tracking.models import EmployeeDevice

        try:
            device = EmployeeDevice.objects.get(device_id=device_id)
            device.fcm_token = fcm_token
            device.push_enabled = True
            device.save(update_fields=['fcm_token', 'push_enabled'])
            return True
        except EmployeeDevice.DoesNotExist:
            return False
