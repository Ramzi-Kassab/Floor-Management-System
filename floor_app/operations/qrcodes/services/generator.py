"""
QR Code and Barcode generation service.

Generates QR codes as PNG/SVG and 1D barcodes for various code formats.
"""
import io
from django.conf import settings
from django.urls import reverse

try:
    import qrcode
    from qrcode.image.svg import SvgImage
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

try:
    import barcode
    from barcode.writer import ImageWriter, SVGWriter
    HAS_BARCODE = True
except ImportError:
    HAS_BARCODE = False


class QRCodeGenerator:
    """
    Service for generating QR codes and barcodes.

    Supports multiple formats:
    - QR Code (2D matrix)
    - Code 128, Code 39 (1D barcode)
    - EAN-13, UPC-A
    - Data Matrix (optional)

    Images can be generated as PNG or SVG.
    """

    # QR code configuration
    DEFAULT_QR_VERSION = 1  # Auto-size
    DEFAULT_QR_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_M if HAS_QRCODE else None
    DEFAULT_QR_BOX_SIZE = 10
    DEFAULT_QR_BORDER = 4

    # Colors
    DEFAULT_FILL_COLOR = "black"
    DEFAULT_BACK_COLOR = "white"

    def __init__(self, base_url=None):
        """
        Initialize generator.

        Args:
            base_url: Base URL for scan endpoints (e.g., 'https://example.com')
                      If None, will use relative URLs
        """
        self.base_url = base_url or ""

    def get_scan_url(self, qcode):
        """
        Get the full URL for a QCode scan endpoint.

        Args:
            qcode: QCode instance

        Returns:
            Full URL string
        """
        path = reverse('qrcodes:scan', kwargs={'token': str(qcode.token)})
        if self.base_url:
            return f"{self.base_url.rstrip('/')}{path}"
        return path

    def generate_qr_png(self, data, box_size=None, border=None,
                        fill_color=None, back_color=None):
        """
        Generate QR code as PNG image.

        Args:
            data: String data to encode
            box_size: Size of each box in pixels (default: 10)
            border: Border size in boxes (default: 4)
            fill_color: QR code color (default: black)
            back_color: Background color (default: white)

        Returns:
            BytesIO object containing PNG image
        """
        if not HAS_QRCODE:
            raise ImportError("qrcode package not installed. Run: pip install qrcode[pil]")

        qr = qrcode.QRCode(
            version=self.DEFAULT_QR_VERSION,
            error_correction=self.DEFAULT_QR_ERROR_CORRECTION,
            box_size=box_size or self.DEFAULT_QR_BOX_SIZE,
            border=border or self.DEFAULT_QR_BORDER,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color=fill_color or self.DEFAULT_FILL_COLOR,
            back_color=back_color or self.DEFAULT_BACK_COLOR
        )

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    def generate_qr_svg(self, data, box_size=None, border=None):
        """
        Generate QR code as SVG image.

        Args:
            data: String data to encode
            box_size: Size of each box (default: 10)
            border: Border size (default: 4)

        Returns:
            BytesIO object containing SVG
        """
        if not HAS_QRCODE:
            raise ImportError("qrcode package not installed. Run: pip install qrcode[pil]")

        qr = qrcode.QRCode(
            version=self.DEFAULT_QR_VERSION,
            error_correction=self.DEFAULT_QR_ERROR_CORRECTION,
            box_size=box_size or self.DEFAULT_QR_BOX_SIZE,
            border=border or self.DEFAULT_QR_BORDER,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(image_factory=SvgImage)

        buffer = io.BytesIO()
        img.save(buffer)
        buffer.seek(0)
        return buffer

    def generate_qr_for_qcode(self, qcode, format='png', **kwargs):
        """
        Generate QR code image for a QCode instance.

        Args:
            qcode: QCode model instance
            format: 'png' or 'svg'
            **kwargs: Additional options for generation

        Returns:
            BytesIO object containing image
        """
        url = self.get_scan_url(qcode)

        if format.lower() == 'svg':
            return self.generate_qr_svg(url, **kwargs)
        else:
            return self.generate_qr_png(url, **kwargs)

    def generate_barcode_png(self, data, barcode_type='code128'):
        """
        Generate 1D barcode as PNG.

        Args:
            data: String data to encode
            barcode_type: Type of barcode ('code128', 'code39', 'ean13', 'upca')

        Returns:
            BytesIO object containing PNG image
        """
        if not HAS_BARCODE:
            raise ImportError("python-barcode package not installed. Run: pip install python-barcode[images]")

        barcode_class = barcode.get_barcode_class(barcode_type)
        code = barcode_class(data, writer=ImageWriter())

        buffer = io.BytesIO()
        code.write(buffer)
        buffer.seek(0)
        return buffer

    def generate_barcode_svg(self, data, barcode_type='code128'):
        """
        Generate 1D barcode as SVG.

        Args:
            data: String data to encode
            barcode_type: Type of barcode ('code128', 'code39', 'ean13', 'upca')

        Returns:
            BytesIO object containing SVG
        """
        if not HAS_BARCODE:
            raise ImportError("python-barcode package not installed. Run: pip install python-barcode")

        barcode_class = barcode.get_barcode_class(barcode_type)
        code = barcode_class(data, writer=SVGWriter())

        buffer = io.BytesIO()
        code.write(buffer)
        buffer.seek(0)
        return buffer

    def generate_label_with_qr(self, qcode, label_text=None,
                                include_token=True, size='medium'):
        """
        Generate a label with QR code and text.

        Args:
            qcode: QCode instance
            label_text: Text to display (defaults to qcode.label)
            include_token: Include short token ID
            size: 'small', 'medium', or 'large'

        Returns:
            BytesIO object containing PNG image
        """
        if not HAS_QRCODE:
            raise ImportError("qrcode package not installed. Run: pip install qrcode[pil]")

        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            raise ImportError("Pillow package not installed. Run: pip install Pillow")

        # Size configurations
        sizes = {
            'small': {'qr_box': 6, 'label_height': 30, 'font_size': 12},
            'medium': {'qr_box': 10, 'label_height': 50, 'font_size': 16},
            'large': {'qr_box': 14, 'label_height': 70, 'font_size': 20},
        }
        config = sizes.get(size, sizes['medium'])

        # Generate QR code
        qr_buffer = self.generate_qr_for_qcode(
            qcode,
            format='png',
            box_size=config['qr_box']
        )
        qr_img = Image.open(qr_buffer)

        # Create label text
        if not label_text:
            label_text = qcode.label or str(qcode)

        # Create combined image
        label_height = config['label_height']
        combined = Image.new(
            'RGB',
            (qr_img.width, qr_img.height + label_height),
            'white'
        )

        # Paste QR code
        combined.paste(qr_img, (0, 0))

        # Add text
        draw = ImageDraw.Draw(combined)

        try:
            font = ImageFont.truetype("arial.ttf", config['font_size'])
        except Exception:
            font = ImageFont.load_default()

        # Center text
        text_bbox = draw.textbbox((0, 0), label_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (combined.width - text_width) // 2
        text_y = qr_img.height + 5

        draw.text((text_x, text_y), label_text, fill='black', font=font)

        # Add token if requested
        if include_token:
            token_text = f"ID: {qcode.token_short}"
            token_bbox = draw.textbbox((0, 0), token_text, font=font)
            token_width = token_bbox[2] - token_bbox[0]
            token_x = (combined.width - token_width) // 2
            token_y = text_y + config['font_size'] + 5
            draw.text((token_x, token_y), token_text, fill='gray', font=font)

        # Save to buffer
        buffer = io.BytesIO()
        combined.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    @staticmethod
    def check_dependencies():
        """
        Check if required packages are installed.

        Returns:
            Dict with status of each dependency
        """
        result = {
            'qrcode': HAS_QRCODE,
            'barcode': HAS_BARCODE,
            'pillow': False,
        }

        try:
            import PIL
            result['pillow'] = True
        except ImportError:
            pass

        return result

    @staticmethod
    def get_install_instructions():
        """
        Get pip install instructions for missing dependencies.

        Returns:
            String with pip install commands
        """
        commands = []

        if not HAS_QRCODE:
            commands.append("pip install qrcode[pil]")
        if not HAS_BARCODE:
            commands.append("pip install python-barcode[images]")

        if commands:
            return "\n".join(commands)
        return "All dependencies are installed."
