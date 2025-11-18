"""
QR Code Generator

Handles actual QR code image generation using qrcode library.
"""

import qrcode
from qrcode.image.pil import PilImage
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile


class QRCodeGenerator:
    """
    Generate QR code images.

    Uses qrcode library to create QR code images with optional branding.
    """

    @staticmethod
    def generate_image(
        data: str,
        size: int = 300,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        border: int = 4,
        include_text: bool = False,
        text: str = ''
    ) -> ContentFile:
        """
        Generate QR code image.

        Args:
            data: Data to encode in QR code
            size: Image size in pixels
            error_correction: Error correction level (L, M, Q, H)
            border: Border size in boxes
            include_text: Include text below QR code?
            text: Text to include

        Returns:
            ContentFile with PNG image data
        """
        # Create QR code
        qr = qrcode.QRCode(
            version=None,  # Auto-determine version
            error_correction=error_correction,
            box_size=10,
            border=border,
        )

        qr.add_data(data)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Resize to desired size
        img = img.resize((size, size), Image.LANCZOS)

        # Add text if requested
        if include_text and text:
            img = QRCodeGenerator._add_text_to_image(img, text)

        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return ContentFile(buffer.read())

    @staticmethod
    def _add_text_to_image(img: Image.Image, text: str, font_size: int = 20) -> Image.Image:
        """
        Add text below QR code image.

        Args:
            img: PIL Image
            text: Text to add
            font_size: Font size

        Returns:
            New Image with text
        """
        # Calculate new image size
        padding = 20
        text_height = font_size + padding * 2
        new_height = img.height + text_height

        # Create new image
        new_img = Image.new('RGB', (img.width, new_height), color='white')

        # Paste QR code
        new_img.paste(img, (0, 0))

        # Add text
        draw = ImageDraw.Draw(new_img)

        try:
            # Try to load a nice font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            # Fallback to default font
            font = ImageFont.load_default()

        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (img.width - text_width) // 2
        text_y = img.height + padding

        # Draw text
        draw.text((text_x, text_y), text, fill='black', font=font)

        return new_img

    @staticmethod
    def generate_with_logo(
        data: str,
        logo_path: str,
        size: int = 300,
        logo_size_ratio: float = 0.25
    ) -> ContentFile:
        """
        Generate QR code with logo in center.

        Args:
            data: Data to encode
            logo_path: Path to logo image file
            size: QR code size
            logo_size_ratio: Logo size as ratio of QR code size (0.0-1.0)

        Returns:
            ContentFile with PNG image
        """
        # Generate base QR code with high error correction
        # (allows for logo to cover part of QR code)
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size), Image.LANCZOS)

        # Open logo
        logo = Image.open(logo_path)

        # Calculate logo size
        logo_size = int(size * logo_size_ratio)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

        # Calculate position (center)
        logo_pos = ((size - logo_size) // 2, (size - logo_size) // 2)

        # Paste logo
        img.paste(logo, logo_pos)

        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return ContentFile(buffer.read())

    @staticmethod
    def generate_batch_sheet(
        qr_codes_data: list,
        layout: str = 'grid',
        qr_size: int = 150,
        columns: int = 4,
        include_labels: bool = True
    ) -> BytesIO:
        """
        Generate a sheet with multiple QR codes (for printing).

        Args:
            qr_codes_data: List of dicts with 'code' and optional 'label'
            layout: 'grid' or 'rows'
            qr_size: Size of each QR code in pixels
            columns: Number of columns
            include_labels: Include labels under QR codes?

        Returns:
            BytesIO with PNG image

        Example:
            qr_data = [
                {'code': 'QR-001', 'label': 'Cutter #1'},
                {'code': 'QR-002', 'label': 'Cutter #2'},
                ...
            ]
            sheet = QRCodeGenerator.generate_batch_sheet(qr_data, columns=4)
        """
        # Calculate dimensions
        margin = 20
        label_height = 30 if include_labels else 0
        cell_height = qr_size + label_height + margin

        rows = (len(qr_codes_data) + columns - 1) // columns

        sheet_width = columns * qr_size + (columns + 1) * margin
        sheet_height = rows * cell_height + margin

        # Create sheet image
        sheet = Image.new('RGB', (sheet_width, sheet_height), color='white')
        draw = ImageDraw.Draw(sheet)

        # Load font for labels
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font = ImageFont.load_default()

        # Generate and place QR codes
        for idx, qr_data in enumerate(qr_codes_data):
            row = idx // columns
            col = idx % columns

            # Generate QR code
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=5,
                border=2,
            )
            qr.add_data(qr_data['code'])
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

            # Calculate position
            x = margin + col * (qr_size + margin)
            y = margin + row * cell_height

            # Paste QR code
            sheet.paste(qr_img, (x, y))

            # Add label if requested
            if include_labels and 'label' in qr_data:
                label_text = qr_data['label']
                bbox = draw.textbbox((0, 0), label_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = x + (qr_size - text_width) // 2
                text_y = y + qr_size + 5

                draw.text((text_x, text_y), label_text, fill='black', font=font)

        # Save to BytesIO
        buffer = BytesIO()
        sheet.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer
