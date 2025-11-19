"""
QR Code Service

Main service for QR code operations.

Handles:
- Generating QR codes for any object
- Scanning and decoding QR codes
- Logging scans
- Tracking usage
- Integration with GPS and device tracking
"""

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from typing import Optional, Dict, Any, Tuple
import io

from floor_app.operations.qr_system.models import QRCode, QRScanLog


class QRCodeService:
    """
    Main QR code service.

    Provides high-level API for QR code operations.
    """

    @classmethod
    def generate_for_object(
        cls,
        obj: Any,
        qr_type: str,
        title: str = '',
        description: str = '',
        size: int = 300,
        prefix: str = 'QR'
    ) -> QRCode:
        """
        Generate a QR code for any Django model instance.

        Args:
            obj: Django model instance to generate QR for
            qr_type: QR code type (from QRCode.QR_TYPES)
            title: Human-readable title
            description: Description
            size: QR code image size in pixels
            prefix: Code prefix for generation

        Returns:
            QRCode instance

        Example:
            serial_unit = SerialUnit.objects.get(id=123)
            qr = QRCodeService.generate_for_object(
                serial_unit,
                'CUTTER',
                title=f"Cutter {serial_unit.serial_number}",
                description="PDC-13-5 Cutter"
            )
        """
        from floor_app.operations.qr_system.services.qr_generator import QRCodeGenerator

        # Get content type
        content_type = ContentType.objects.get_for_model(obj)

        # Check if QR code already exists
        existing_qr = QRCode.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
            is_active=True
        ).first()

        if existing_qr:
            return existing_qr

        # Generate unique code
        code = QRCode.generate_code(prefix)

        # Create QR code record
        qr_code = QRCode.objects.create(
            code=code,
            qr_type=qr_type,
            content_type=content_type,
            object_id=obj.pk,
            title=title or str(obj),
            description=description,
            qr_size=size
        )

        # Generate QR code image
        qr_image_file = QRCodeGenerator.generate_image(code, size)
        qr_code.qr_image.save(f'{code}.png', qr_image_file, save=True)

        return qr_code

    @classmethod
    def scan(
        cls,
        code: str,
        user=None,
        employee=None,
        context: str = 'INFO',
        gps_location: Optional[Dict[str, float]] = None,
        device_info: Optional[Dict[str, Any]] = None,
        action_taken: str = '',
        notes: str = ''
    ) -> Tuple[bool, str, Optional[Any]]:
        """
        Scan a QR code and return the related object.

        Args:
            code: QR code value
            user: User who scanned (optional)
            employee: Employee who scanned (optional)
            context: Scan context (from QRScanLog.SCAN_CONTEXTS)
            gps_location: GPS location dict with 'latitude', 'longitude', 'accuracy'
            device_info: Device information dict
            action_taken: Action taken after scan
            notes: Optional notes

        Returns:
            Tuple of (success, message, related_object)

        Example:
            success, msg, serial_unit = QRCodeService.scan(
                'QR-20250118-A3F9D2',
                user=request.user,
                context='PRODUCTION',
                gps_location={'latitude': 24.1234, 'longitude': 55.5678, 'accuracy': 10},
                action_taken='Added to BOM map cell B1P3P'
            )
        """
        try:
            # Get QR code
            qr_code = QRCode.objects.select_related('content_type').get(code=code)

            # Check if valid
            if not qr_code.is_valid:
                if qr_code.is_expired:
                    return False, "QR code has expired", None
                else:
                    return False, "QR code has been deactivated", None

            # Get related object
            related_object = qr_code.related_object

            # Log the scan
            scan_log = cls._log_scan(
                qr_code=qr_code,
                user=user,
                employee=employee,
                context=context,
                gps_location=gps_location,
                device_info=device_info,
                action_taken=action_taken,
                notes=notes
            )

            # Update QR code scan count
            qr_code.increment_scan_count(user)

            # Perform context-specific actions
            cls._handle_scan_context(qr_code, related_object, context, scan_log)

            return True, f"Successfully scanned {qr_code.get_qr_type_display()}", related_object

        except QRCode.DoesNotExist:
            return False, "QR code not found", None
        except Exception as e:
            return False, f"Error scanning QR code: {str(e)}", None

    @classmethod
    def _log_scan(
        cls,
        qr_code: QRCode,
        user=None,
        employee=None,
        context: str = 'INFO',
        gps_location: Optional[Dict[str, float]] = None,
        device_info: Optional[Dict[str, Any]] = None,
        action_taken: str = '',
        notes: str = ''
    ) -> QRScanLog:
        """Create a scan log entry."""
        # Reverse geocode if we have GPS
        location_address = ''
        if gps_location and gps_location.get('latitude') and gps_location.get('longitude'):
            # TODO: Integrate with GPS service for reverse geocoding
            location_address = ''

        # Create log
        scan_log = QRScanLog.objects.create(
            qr_code=qr_code,
            scanned_by_user=user,
            scanned_by_employee=employee,
            latitude=gps_location.get('latitude') if gps_location else None,
            longitude=gps_location.get('longitude') if gps_location else None,
            gps_accuracy_meters=gps_location.get('accuracy') if gps_location else None,
            location_address=location_address,
            scan_context=context,
            device_info=device_info or {},
            action_taken=action_taken,
            notes=notes
        )

        return scan_log

    @classmethod
    def _handle_scan_context(cls, qr_code, related_object, context, scan_log):
        """
        Perform context-specific actions after scanning.

        Different scan contexts trigger different behaviors.
        """
        if context == 'RECEIVING':
            # Receiving context: might update receiving status
            pass
        elif context == 'PRODUCTION':
            # Production context: might update production status
            pass
        elif context == 'QC':
            # QC context: might trigger QC workflow
            pass
        elif context == 'SHIPPING':
            # Shipping context: might update shipping status
            pass
        elif context == 'INVENTORY_CHECK':
            # Inventory check: might log inventory count
            pass
        elif context == 'LOCATION_VERIFY':
            # Location verification: might verify GPS matches expected location
            if scan_log.has_gps_location:
                # TODO: Integrate with GPS verification service
                pass

        # Context-specific logic can be extended here
        pass

    @classmethod
    def get_scan_history(cls, code: str, limit: int = 50) -> list:
        """
        Get scan history for a QR code.

        Args:
            code: QR code value
            limit: Max number of scans to return

        Returns:
            List of QRScanLog instances
        """
        try:
            qr_code = QRCode.objects.get(code=code)
            return list(qr_code.scan_logs.all()[:limit])
        except QRCode.DoesNotExist:
            return []

    @classmethod
    def verify_code(cls, code: str) -> Tuple[bool, str, Optional[QRCode]]:
        """
        Verify if a QR code is valid without logging a scan.

        Args:
            code: QR code value

        Returns:
            Tuple of (is_valid, message, qr_code)
        """
        try:
            qr_code = QRCode.objects.get(code=code)

            if not qr_code.is_active:
                return False, "QR code has been deactivated", qr_code

            if qr_code.is_expired:
                return False, "QR code has expired", qr_code

            return True, "QR code is valid", qr_code

        except QRCode.DoesNotExist:
            return False, "QR code not found", None

    @classmethod
    def regenerate(cls, qr_code: QRCode, reason: str = '') -> QRCode:
        """
        Regenerate a QR code (create new version).

        Useful when QR code is damaged, lost, or needs updating.

        Args:
            qr_code: Existing QR code to regenerate
            reason: Reason for regeneration

        Returns:
            New QRCode instance
        """
        from floor_app.operations.qr_system.services.qr_generator import QRCodeGenerator

        # Deactivate old QR code
        qr_code.deactivate(reason=f"Regenerated: {reason}")

        # Generate new code
        new_code = QRCode.generate_code()

        # Create new QR code
        new_qr = QRCode.objects.create(
            code=new_code,
            qr_type=qr_code.qr_type,
            content_type=qr_code.content_type,
            object_id=qr_code.object_id,
            title=qr_code.title,
            description=qr_code.description,
            qr_size=qr_code.qr_size,
            version=qr_code.version + 1,
            previous_version=qr_code
        )

        # Generate new image
        qr_image_file = QRCodeGenerator.generate_image(new_code, qr_code.qr_size)
        new_qr.qr_image.save(f'{new_code}.png', qr_image_file, save=True)

        return new_qr

    @classmethod
    def bulk_generate(
        cls,
        objects: list,
        qr_type: str,
        batch_number: str = None,
        purpose: str = ''
    ) -> list:
        """
        Generate QR codes for multiple objects.

        Args:
            objects: List of Django model instances
            qr_type: QR code type
            batch_number: Optional batch number
            purpose: Purpose of this batch

        Returns:
            List of QRCode instances
        """
        from floor_app.operations.qr_system.models import QRBatch

        # Create batch if batch_number provided
        batch = None
        if batch_number:
            batch = QRBatch.objects.create(
                batch_number=batch_number,
                qr_type=qr_type,
                quantity=len(objects),
                purpose=purpose
            )

        # Generate QR codes
        qr_codes = []
        for obj in objects:
            qr = cls.generate_for_object(obj, qr_type)
            qr_codes.append(qr)

        # Update batch
        if batch:
            batch.generated_count = len(qr_codes)
            batch.is_complete = True
            batch.completed_at = timezone.now()
            batch.save()

        return qr_codes

    @classmethod
    def get_qr_for_object(cls, obj: Any) -> Optional[QRCode]:
        """
        Get active QR code for an object.

        Args:
            obj: Django model instance

        Returns:
            QRCode instance or None
        """
        content_type = ContentType.objects.get_for_model(obj)
        return QRCode.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
            is_active=True
        ).first()

    @classmethod
    def get_or_create_qr(
        cls,
        obj: Any,
        qr_type: str,
        title: str = '',
        description: str = ''
    ) -> QRCode:
        """
        Get existing QR code or create new one.

        Args:
            obj: Django model instance
            qr_type: QR code type
            title: Title (used only if creating)
            description: Description (used only if creating)

        Returns:
            QRCode instance
        """
        existing_qr = cls.get_qr_for_object(obj)
        if existing_qr:
            return existing_qr

        return cls.generate_for_object(obj, qr_type, title, description)
