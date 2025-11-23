"""
QR Code Utilities for HR

Helper functions to generate and manage QR codes for employees and assets.
"""
from django.urls import reverse
from qrcodes.services import QRCodeGenerator
from qrcodes.models import QCode, QCodeType
import json


def get_or_create_employee_qr(employee):
    """
    Get or create QR code for an employee.
    
    Returns the QCode object.
    """
    # Try to find existing QR code
    try:
        qcode = QCode.objects.get(
            qcode_type__code='EMPLOYEE',
            reference_id=str(employee.pk),
            is_active=True
        )
        return qcode
    except QCode.DoesNotExist:
        pass
    
    # Get or create Employee QCodeType
    qcode_type, _ = QCodeType.objects.get_or_create(
        code='EMPLOYEE',
        defaults={
            'name': 'Employee',
            'description': 'Employee identification QR code',
            'requires_confirmation': False,
        }
    )
    
    # Create QR code data
    qr_data = {
        'type': 'employee',
        'employee_id': employee.pk,
        'employee_code': employee.employee_code,
        'name': employee.person.full_name,
        'url': reverse('hr:employee-detail', kwargs={'pk': employee.pk})
    }
    
    # Generate QR code
    generator = QRCodeGenerator()
    qcode = generator.generate_qcode(
        qcode_type=qcode_type,
        reference_id=str(employee.pk),
        data=qr_data,
        description=f"QR Code for {employee.person.full_name}"
    )
    
    return qcode


def get_or_create_asset_qr(asset):
    """
    Get or create QR code for an asset.
    
    Returns the QCode object.
    """
    # Try to find existing QR code
    try:
        qcode = QCode.objects.get(
            qcode_type__code='ASSET',
            reference_id=str(asset.pk),
            is_active=True
        )
        return qcode
    except QCode.DoesNotExist:
        pass
    
    # Get or create Asset QCodeType
    qcode_type, _ = QCodeType.objects.get_or_create(
        code='ASSET',
        defaults={
            'name': 'Asset',
            'description': 'Company asset QR code',
            'requires_confirmation': False,
        }
    )
    
    # Create QR code data
    qr_data = {
        'type': 'asset',
        'asset_id': asset.pk,
        'asset_tag': asset.asset_tag,
        'name': asset.name,
        'asset_type': asset.asset_type.name,
        'url': reverse('hr:asset_detail', kwargs={'pk': asset.pk})
    }
    
    # Generate QR code
    generator = QRCodeGenerator()
    qcode = generator.generate_qcode(
        qcode_type=qcode_type,
        reference_id=str(asset.pk),
        data=qr_data,
        description=f"QR Code for {asset.asset_tag}"
    )
    
    return qcode


def generate_employee_qr_image(employee):
    """Generate QR code image for employee."""
    qcode = get_or_create_employee_qr(employee)
    generator = QRCodeGenerator()
    return generator.generate_image(qcode.qr_data)


def generate_asset_qr_image(asset):
    """Generate QR code image for asset."""
    qcode = get_or_create_asset_qr(asset)
    generator = QRCodeGenerator()
    return generator.generate_image(qcode.qr_data)
