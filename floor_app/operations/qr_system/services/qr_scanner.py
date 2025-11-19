"""
QR Code Scanner Service

Service for scanning and decoding QR codes.
"""
from typing import Dict, Any, Optional
import json
from django.utils import timezone


class QRCodeScanner:
    """
    Service for scanning and decoding QR codes.

    Handles QR code scanning, validation, and context-aware actions.
    """

    @staticmethod
    def decode_qr_data(qr_data: str) -> Dict[str, Any]:
        """
        Decode QR code data.

        Args:
            qr_data: Raw QR code data string

        Returns:
            Dict containing decoded QR data
        """
        try:
            # Try to parse as JSON
            data = json.loads(qr_data)
            return {
                'success': True,
                'data': data,
                'format': 'json'
            }
        except json.JSONDecodeError:
            # Plain text QR code
            return {
                'success': True,
                'data': {'text': qr_data},
                'format': 'text'
            }

    @staticmethod
    def validate_qr_code(qr_code_id: str) -> Dict[str, Any]:
        """
        Validate a QR code exists and is active.

        Args:
            qr_code_id: QR code identifier

        Returns:
            Dict with validation results
        """
        from floor_app.operations.qr_system.models import QRCode

        try:
            qr_code = QRCode.objects.get(qr_code=qr_code_id)

            if not qr_code.is_active:
                return {
                    'valid': False,
                    'error': 'QR code is inactive',
                    'qr_code': None
                }

            if qr_code.expires_at and qr_code.expires_at < timezone.now():
                return {
                    'valid': False,
                    'error': 'QR code has expired',
                    'qr_code': None
                }

            return {
                'valid': True,
                'qr_code': qr_code,
                'error': None
            }

        except QRCode.DoesNotExist:
            return {
                'valid': False,
                'error': 'QR code not found',
                'qr_code': None
            }

    @staticmethod
    def log_scan(qr_code, scanned_by=None, context: Optional[Dict] = None):
        """
        Log a QR code scan.

        Args:
            qr_code: QRCode instance
            scanned_by: User who scanned the code
            context: Additional scan context
        """
        from floor_app.operations.qr_system.models import QRScanLog
        from django.utils import timezone

        scan_log = QRScanLog.objects.create(
            qr_code=qr_code,
            scanned_by=scanned_by,
            scanned_at=timezone.now(),
            scan_context=context or {}
        )

        # Update QR code last scanned timestamp
        qr_code.last_scanned_at = timezone.now()
        qr_code.scan_count += 1
        qr_code.save(update_fields=['last_scanned_at', 'scan_count'])

        return scan_log

    @classmethod
    def scan_and_process(cls, qr_data: str, scanned_by=None, context: Optional[Dict] = None):
        """
        Complete scan workflow: decode, validate, log, and return results.

        Args:
            qr_data: Raw QR code data
            scanned_by: User who scanned
            context: Scan context

        Returns:
            Dict with scan results and QR code object
        """
        # Decode QR data
        decoded = cls.decode_qr_data(qr_data)
        if not decoded['success']:
            return {
                'success': False,
                'error': 'Could not decode QR code',
                'qr_code': None
            }

        # Extract QR code ID
        if decoded['format'] == 'json':
            qr_code_id = decoded['data'].get('qr_code') or decoded['data'].get('id')
        else:
            qr_code_id = decoded['data'].get('text')

        if not qr_code_id:
            return {
                'success': False,
                'error': 'QR code ID not found in data',
                'qr_code': None
            }

        # Validate QR code
        validation = cls.validate_qr_code(qr_code_id)
        if not validation['valid']:
            return {
                'success': False,
                'error': validation['error'],
                'qr_code': None
            }

        # Log the scan
        scan_log = cls.log_scan(validation['qr_code'], scanned_by, context)

        return {
            'success': True,
            'qr_code': validation['qr_code'],
            'scan_log': scan_log,
            'decoded_data': decoded['data']
        }
