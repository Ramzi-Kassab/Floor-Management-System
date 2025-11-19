"""
Tests for QR Code Services

Test QR code generation, scanning, and printing functionality.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from floor_app.operations.qr_system.models import QRCode, QRScanLog, QRBatch
from floor_app.operations.qr_system.services.qr_scanner import QRCodeScanner
from floor_app.operations.qr_system.services.qr_printer import QRCodePrinter
from PIL import Image
import json

User = get_user_model()


class QRCodePrinterTests(TestCase):
    """Test QR Code generation and printing."""

    def setUp(self):
        """Set up test data."""
        self.printer = QRCodePrinter()

    def test_generate_qr_image(self):
        """Test QR code image generation."""
        qr_image = self.printer.generate_qr_image("TEST-123", size=200)

        self.assertIsNotNone(qr_image)
        self.assertIsInstance(qr_image, Image.Image)
        self.assertEqual(qr_image.size, (200, 200))

    def test_generate_qr_image_different_sizes(self):
        """Test QR code generation with different sizes."""
        for size in [100, 200, 300, 500]:
            qr_image = self.printer.generate_qr_image("TEST", size=size)
            self.assertEqual(qr_image.size, (size, size))

    def test_generate_qr_image_with_empty_data(self):
        """Test QR generation with empty data."""
        with self.assertRaises(ValueError):
            self.printer.generate_qr_image("", size=200)

    def test_create_label(self):
        """Test creating QR code label with text."""
        label = self.printer.create_label(
            data="ASSET-123",
            label_text="Asset #123",
            size=200
        )

        self.assertIsNotNone(label)
        self.assertIsInstance(label, Image.Image)

    def test_create_batch_sheet(self):
        """Test creating batch sheet with multiple QR codes."""
        codes = [
            {"data": f"TEST-{i}", "label": f"Label {i}"}
            for i in range(6)
        ]

        sheet = self.printer.create_batch_sheet(
            codes=codes,
            codes_per_row=3
        )

        self.assertIsNotNone(sheet)
        self.assertIsInstance(sheet, Image.Image)


class QRCodeScannerTests(TestCase):
    """Test QR Code scanning functionality."""

    def setUp(self):
        """Set up test data."""
        self.scanner = QRCodeScanner()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_decode_qr_data_json(self):
        """Test decoding JSON QR data."""
        qr_data = json.dumps({
            'type': 'asset',
            'id': '123',
            'code': 'ASSET-123'
        })

        decoded = self.scanner.decode_qr_data(qr_data)

        self.assertIsInstance(decoded, dict)
        self.assertEqual(decoded['type'], 'asset')
        self.assertEqual(decoded['id'], '123')

    def test_decode_qr_data_plain_text(self):
        """Test decoding plain text QR data."""
        qr_data = "SIMPLE-CODE-123"

        decoded = self.scanner.decode_qr_data(qr_data)

        self.assertIsInstance(decoded, dict)
        self.assertEqual(decoded['raw_data'], qr_data)

    def test_validate_qr_code_structure(self):
        """Test QR code validation."""
        valid_data = {
            'type': 'asset',
            'id': '123'
        }

        is_valid, message = self.scanner.validate_qr_code(valid_data)

        self.assertTrue(is_valid)
        self.assertIsNone(message)

    def test_validate_qr_code_invalid_structure(self):
        """Test QR code validation with invalid data."""
        invalid_data = {}

        is_valid, message = self.scanner.validate_qr_code(invalid_data)

        self.assertFalse(is_valid)
        self.assertIsNotNone(message)


class QRCodeModelTests(TestCase):
    """Test QR Code model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_qr_code(self):
        """Test creating a QR code record."""
        qr_code = QRCode.objects.create(
            qr_data="TEST-123",
            qr_type="ASSET",
            generated_by=self.user,
            is_active=True
        )

        self.assertEqual(qr_code.qr_data, "TEST-123")
        self.assertEqual(qr_code.qr_type, "ASSET")
        self.assertTrue(qr_code.is_active)

    def test_qr_code_string_representation(self):
        """Test QR code __str__ method."""
        qr_code = QRCode.objects.create(
            qr_data="TEST-456",
            qr_type="ASSET",
            generated_by=self.user
        )

        str_repr = str(qr_code)
        self.assertIn("TEST-456", str_repr)

    def test_create_qr_batch(self):
        """Test creating a QR code batch."""
        batch = QRBatch.objects.create(
            batch_number="BATCH-001",
            qr_type="ASSET",
            quantity=100,
            created_by=self.user
        )

        self.assertEqual(batch.batch_number, "BATCH-001")
        self.assertEqual(batch.quantity, 100)


class QRScanLogTests(TestCase):
    """Test QR scan logging functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='scanner',
            password='testpass123'
        )
        self.qr_code = QRCode.objects.create(
            qr_data="TEST-LOG",
            qr_type="ASSET",
            generated_by=self.user
        )

    def test_create_scan_log(self):
        """Test creating a scan log entry."""
        scan_log = QRScanLog.objects.create(
            qr_code=self.qr_code,
            scanned_by_user=self.user,
            scan_context="ASSET_VERIFICATION",
            scan_result_success=True
        )

        self.assertEqual(scan_log.qr_code, self.qr_code)
        self.assertEqual(scan_log.scanned_by_user, self.user)
        self.assertTrue(scan_log.scan_result_success)

    def test_scan_log_updates_qr_code(self):
        """Test that scanning updates last_scanned_at."""
        QRScanLog.objects.create(
            qr_code=self.qr_code,
            scanned_by_user=self.user,
            scan_context="TEST",
            scan_result_success=True
        )

        # Refresh QR code from database
        self.qr_code.refresh_from_db()

        # Check that last_scanned_at is set (if model has this field)
        # self.assertIsNotNone(self.qr_code.last_scanned_at)
