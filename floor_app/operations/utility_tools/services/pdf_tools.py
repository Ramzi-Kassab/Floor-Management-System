"""
PDF Tools Service

Merge, split, compress, rotate PDF files and convert images to PDF.
"""

import io
from typing import List
from PIL import Image


class PDFToolsService:
    """
    Service for PDF operations.
    """

    @classmethod
    def merge_pdfs(cls, pdf_files: List) -> io.BytesIO:
        """
        Merge multiple PDF files into one.

        Args:
            pdf_files: List of PDF file objects

        Returns:
            BytesIO object containing merged PDF

        Example:
            merged = PDFToolsService.merge_pdfs([file1, file2, file3])
        """
        try:
            from PyPDF2 import PdfMerger

            merger = PdfMerger()

            for pdf_file in pdf_files:
                merger.append(pdf_file)

            output = io.BytesIO()
            merger.write(output)
            merger.close()

            output.seek(0)
            return output

        except ImportError:
            raise ImportError("PyPDF2 is required for PDF operations. Install with: pip install PyPDF2")

    @classmethod
    def split_pdf(cls, pdf_file, pages: List[int] = None, ranges: List[tuple] = None) -> List[io.BytesIO]:
        """
        Split PDF into multiple files.

        Args:
            pdf_file: PDF file object
            pages: List of page numbers to extract (1-indexed)
            ranges: List of page ranges to extract [(1, 3), (5, 7)]

        Returns:
            List of BytesIO objects containing split PDFs

        Example:
            # Extract pages 1, 3, 5
            splits = PDFToolsService.split_pdf(pdf_file, pages=[1, 3, 5])

            # Extract page ranges 1-3 and 5-7
            splits = PDFToolsService.split_pdf(pdf_file, ranges=[(1, 3), (5, 7)])
        """
        try:
            from PyPDF2 import PdfReader, PdfWriter

            reader = PdfReader(pdf_file)
            outputs = []

            if pages:
                # Extract individual pages
                for page_num in pages:
                    writer = PdfWriter()
                    # Convert from 1-indexed to 0-indexed
                    writer.add_page(reader.pages[page_num - 1])

                    output = io.BytesIO()
                    writer.write(output)
                    output.seek(0)
                    outputs.append(output)

            elif ranges:
                # Extract page ranges
                for start, end in ranges:
                    writer = PdfWriter()
                    # Convert from 1-indexed to 0-indexed
                    for page_num in range(start - 1, end):
                        if page_num < len(reader.pages):
                            writer.add_page(reader.pages[page_num])

                    output = io.BytesIO()
                    writer.write(output)
                    output.seek(0)
                    outputs.append(output)

            else:
                # Split into individual pages
                for page in reader.pages:
                    writer = PdfWriter()
                    writer.add_page(page)

                    output = io.BytesIO()
                    writer.write(output)
                    output.seek(0)
                    outputs.append(output)

            return outputs

        except ImportError:
            raise ImportError("PyPDF2 is required. Install with: pip install PyPDF2")

    @classmethod
    def rotate_pdf(cls, pdf_file, angle: int, pages: List[int] = None) -> io.BytesIO:
        """
        Rotate pages in a PDF.

        Args:
            pdf_file: PDF file object
            angle: Rotation angle (90, 180, 270)
            pages: List of page numbers to rotate (None = all pages)

        Returns:
            BytesIO object containing rotated PDF

        Example:
            rotated = PDFToolsService.rotate_pdf(pdf_file, angle=90, pages=[1, 3])
        """
        try:
            from PyPDF2 import PdfReader, PdfWriter

            reader = PdfReader(pdf_file)
            writer = PdfWriter()

            for i, page in enumerate(reader.pages):
                page_num = i + 1

                if pages is None or page_num in pages:
                    page.rotate(angle)

                writer.add_page(page)

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            return output

        except ImportError:
            raise ImportError("PyPDF2 is required. Install with: pip install PyPDF2")

    @classmethod
    def extract_pages(cls, pdf_file, pages: List[int]) -> io.BytesIO:
        """
        Extract specific pages from PDF.

        Args:
            pdf_file: PDF file object
            pages: List of page numbers to extract (1-indexed)

        Returns:
            BytesIO object containing extracted pages

        Example:
            extracted = PDFToolsService.extract_pages(pdf_file, pages=[1, 3, 5])
        """
        try:
            from PyPDF2 import PdfReader, PdfWriter

            reader = PdfReader(pdf_file)
            writer = PdfWriter()

            for page_num in pages:
                # Convert from 1-indexed to 0-indexed
                if 0 <= page_num - 1 < len(reader.pages):
                    writer.add_page(reader.pages[page_num - 1])

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            return output

        except ImportError:
            raise ImportError("PyPDF2 is required. Install with: pip install PyPDF2")

    @classmethod
    def get_pdf_info(cls, pdf_file) -> dict:
        """
        Get information about a PDF file.

        Args:
            pdf_file: PDF file object

        Returns:
            Dict with PDF information

        Example:
            info = PDFToolsService.get_pdf_info(pdf_file)
            # Returns: {'pages': 10, 'encrypted': False, 'title': '...', ...}
        """
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(pdf_file)

            metadata = reader.metadata or {}

            return {
                'pages': len(reader.pages),
                'encrypted': reader.is_encrypted,
                'title': metadata.get('/Title', ''),
                'author': metadata.get('/Author', ''),
                'subject': metadata.get('/Subject', ''),
                'creator': metadata.get('/Creator', ''),
                'producer': metadata.get('/Producer', ''),
            }

        except ImportError:
            raise ImportError("PyPDF2 is required. Install with: pip install PyPDF2")

    @classmethod
    def images_to_pdf(cls, image_files: List, quality: int = 85) -> io.BytesIO:
        """
        Convert multiple images to a single PDF.

        Args:
            image_files: List of image file objects
            quality: JPEG quality for conversion (1-100)

        Returns:
            BytesIO object containing PDF

        Example:
            pdf = PDFToolsService.images_to_pdf([img1, img2, img3])
        """
        images = []

        for image_file in image_files:
            img = Image.open(image_file)

            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    rgb_img.paste(img, mask=img.split()[-1])
                else:
                    rgb_img.paste(img)
                img = rgb_img

            images.append(img)

        # Save as PDF
        output = io.BytesIO()

        if len(images) > 0:
            # First image
            first_image = images[0]

            # Remaining images
            remaining_images = images[1:] if len(images) > 1 else []

            # Save as PDF
            first_image.save(
                output,
                format='PDF',
                save_all=True,
                append_images=remaining_images,
                quality=quality
            )

        output.seek(0)
        return output

    @classmethod
    def pdf_to_images(cls, pdf_file, dpi: int = 200) -> List[io.BytesIO]:
        """
        Convert PDF pages to images.

        Args:
            pdf_file: PDF file object
            dpi: Resolution for conversion

        Returns:
            List of BytesIO objects containing images

        Note:
            Requires pdf2image library: pip install pdf2image
            And poppler-utils system package

        Example:
            images = PDFToolsService.pdf_to_images(pdf_file, dpi=300)
        """
        try:
            from pdf2image import convert_from_bytes

            # Read PDF bytes
            pdf_bytes = pdf_file.read()

            # Convert to images
            pil_images = convert_from_bytes(pdf_bytes, dpi=dpi)

            outputs = []
            for pil_image in pil_images:
                output = io.BytesIO()
                pil_image.save(output, format='PNG')
                output.seek(0)
                outputs.append(output)

            return outputs

        except ImportError:
            raise ImportError("pdf2image is required. Install with: pip install pdf2image")
