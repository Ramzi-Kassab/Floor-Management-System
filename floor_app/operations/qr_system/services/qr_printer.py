"""
QR Code Printer Service

Service for printing QR codes (labels, sheets, batches).
"""
from typing import List, Dict, Any, Optional
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode


class QRCodePrinter:
    """
    Service for generating printable QR code labels and sheets.

    Supports various label formats and batch printing.
    """

    # Standard label sizes (in mm)
    LABEL_SIZES = {
        'small': (25, 25),      # 25mm x 25mm
        'medium': (50, 50),     # 50mm x 50mm
        'large': (75, 75),      # 75mm x 75mm
        'badge': (85, 54),      # Credit card size
    }

    @staticmethod
    def generate_qr_image(data: str, size: int = 300, border: int = 2) -> Image:
        """
        Generate a QR code image.

        Args:
            data: Data to encode
            size: Image size in pixels
            border: Border size in boxes

        Returns:
            PIL Image object
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Resize to desired size
        img = img.resize((size, size), Image.Resampling.LANCZOS)

        return img

    @classmethod
    def create_label(
        cls,
        qr_code_data: str,
        label_text: Optional[str] = None,
        size: str = 'medium',
        include_border: bool = True
    ) -> BytesIO:
        """
        Create a printable QR code label with optional text.

        Args:
            qr_code_data: Data to encode in QR
            label_text: Text to display below QR code
            size: Label size ('small', 'medium', 'large', 'badge')
            include_border: Include border around label

        Returns:
            BytesIO containing PNG image
        """
        # Get label dimensions
        width_mm, height_mm = cls.LABEL_SIZES.get(size, cls.LABEL_SIZES['medium'])

        # Convert mm to pixels (assuming 300 DPI)
        dpi = 300
        width_px = int(width_mm * dpi / 25.4)
        height_px = int(height_mm * dpi / 25.4)

        # Create blank label
        label = Image.new('RGB', (width_px, height_px), 'white')
        draw = ImageDraw.Draw(label)

        # Generate QR code (80% of label width)
        qr_size = int(width_px * 0.8)
        qr_img = cls.generate_qr_image(qr_code_data, qr_size)

        # Center QR code
        qr_x = (width_px - qr_size) // 2
        qr_y = int(height_px * 0.1)  # 10% from top
        label.paste(qr_img, (qr_x, qr_y))

        # Add text if provided
        if label_text:
            try:
                # Try to use a nice font
                font_size = int(height_px * 0.05)
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                # Fall back to default font
                font = ImageFont.load_default()

            # Center text below QR code
            text_bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (width_px - text_width) // 2
            text_y = qr_y + qr_size + int(height_px * 0.05)

            draw.text((text_x, text_y), label_text, fill='black', font=font)

        # Add border if requested
        if include_border:
            border_width = int(width_px * 0.01)
            draw.rectangle(
                [(border_width, border_width), (width_px - border_width, height_px - border_width)],
                outline='black',
                width=border_width
            )

        # Save to BytesIO
        output = BytesIO()
        label.save(output, format='PNG', dpi=(dpi, dpi))
        output.seek(0)

        return output

    @classmethod
    def create_batch_sheet(
        cls,
        qr_codes: List[Dict[str, str]],
        labels_per_row: int = 3,
        labels_per_column: int = 8,
        label_size: str = 'small'
    ) -> BytesIO:
        """
        Create a sheet of multiple QR code labels for batch printing.

        Args:
            qr_codes: List of dicts with 'data' and optional 'text'
            labels_per_row: Number of labels per row
            labels_per_column: Number of labels per column
            label_size: Size of each label

        Returns:
            BytesIO containing PNG image of full sheet
        """
        # A4 size at 300 DPI
        dpi = 300
        sheet_width = int(210 * dpi / 25.4)   # 210mm
        sheet_height = int(297 * dpi / 25.4)  # 297mm

        # Create blank sheet
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')

        # Calculate label dimensions
        label_width = sheet_width // labels_per_row
        label_height = sheet_height // labels_per_column

        # Add each QR code
        for idx, qr_data in enumerate(qr_codes[:labels_per_row * labels_per_column]):
            row = idx // labels_per_row
            col = idx % labels_per_row

            # Generate individual label
            label_img_io = cls.create_label(
                qr_data['data'],
                qr_data.get('text'),
                label_size,
                include_border=True
            )
            label_img = Image.open(label_img_io)

            # Resize to fit in grid
            label_img = label_img.resize((label_width, label_height), Image.Resampling.LANCZOS)

            # Paste onto sheet
            x = col * label_width
            y = row * label_height
            sheet.paste(label_img, (x, y))

        # Save sheet to BytesIO
        output = BytesIO()
        sheet.save(output, format='PNG', dpi=(dpi, dpi))
        output.seek(0)

        return output

    @classmethod
    def create_print_job(cls, qr_codes_queryset, job_name: str, user) -> 'QRCodePrintJob':
        """
        Create a print job for a batch of QR codes.

        Args:
            qr_codes_queryset: QuerySet of QRCode objects
            job_name: Name for the print job
            user: User creating the job

        Returns:
            QRCodePrintJob instance
        """
        from floor_app.operations.qr_system.models import QRCodePrintJob
        from django.utils import timezone

        # Prepare QR data for batch sheet
        qr_data_list = []
        for qr_code in qr_codes_queryset:
            qr_data_list.append({
                'data': qr_code.qr_code,
                'text': qr_code.label or qr_code.qr_type
            })

        # Generate batch sheet
        sheet_image = cls.create_batch_sheet(qr_data_list)

        # Create print job
        print_job = QRCodePrintJob.objects.create(
            job_name=job_name,
            created_by=user,
            total_codes=len(qr_data_list),
            status='PENDING'
        )

        # Save the sheet image (you'd typically save to a file or S3)
        # For now, we'll mark it as ready
        print_job.status = 'READY'
        print_job.save()

        return print_job
