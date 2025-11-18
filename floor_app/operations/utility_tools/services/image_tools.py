"""
Image Processing Tools Service

Resize, compress, convert, crop, and rotate images.
"""

from PIL import Image, ImageOps
import io
import base64
from typing import Tuple, Optional


class ImageToolsService:
    """
    Service for image processing operations.
    """

    SUPPORTED_FORMATS = ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP', 'TIFF']

    @classmethod
    def resize_image(
        cls,
        image_file,
        width: Optional[int] = None,
        height: Optional[int] = None,
        maintain_aspect_ratio: bool = True,
        quality: int = 85
    ) -> io.BytesIO:
        """
        Resize an image to specified dimensions.

        Args:
            image_file: Image file object or path
            width: Target width in pixels
            height: Target height in pixels
            maintain_aspect_ratio: Keep original aspect ratio
            quality: Output quality (1-100)

        Returns:
            BytesIO object containing resized image

        Example:
            resized = ImageToolsService.resize_image(
                image_file=uploaded_file,
                width=800,
                height=600,
                maintain_aspect_ratio=True
            )
        """
        # Open image
        img = Image.open(image_file)

        # Get original dimensions
        orig_width, orig_height = img.size

        # Calculate new dimensions
        if maintain_aspect_ratio:
            if width and height:
                # Fit within both dimensions
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                new_width, new_height = img.size
            elif width:
                # Scale to width
                ratio = width / orig_width
                new_height = int(orig_height * ratio)
                img = img.resize((width, new_height), Image.Resampling.LANCZOS)
            elif height:
                # Scale to height
                ratio = height / orig_height
                new_width = int(orig_width * ratio)
                img = img.resize((new_width, height), Image.Resampling.LANCZOS)
            else:
                # No resize needed
                new_width, new_height = orig_width, orig_height
        else:
            # Stretch to exact dimensions
            new_width = width or orig_width
            new_height = height or orig_height
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save to BytesIO
        output = io.BytesIO()
        format = img.format or 'JPEG'

        if format == 'JPEG':
            # Convert RGBA to RGB for JPEG
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            img.save(output, format='JPEG', quality=quality, optimize=True)
        else:
            img.save(output, format=format, optimize=True)

        output.seek(0)
        return output

    @classmethod
    def compress_image(
        cls,
        image_file,
        quality: int = 85,
        max_size_kb: Optional[int] = None
    ) -> io.BytesIO:
        """
        Compress an image to reduce file size.

        Args:
            image_file: Image file object
            quality: Compression quality (1-100)
            max_size_kb: Maximum file size in KB (will reduce quality if needed)

        Returns:
            BytesIO object containing compressed image

        Example:
            compressed = ImageToolsService.compress_image(
                image_file=uploaded_file,
                quality=75,
                max_size_kb=500
            )
        """
        img = Image.open(image_file)

        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        output = io.BytesIO()

        # If max_size specified, iteratively reduce quality
        if max_size_kb:
            current_quality = quality
            while current_quality > 10:
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=current_quality, optimize=True)

                size_kb = len(output.getvalue()) / 1024
                if size_kb <= max_size_kb:
                    break

                current_quality -= 5
        else:
            img.save(output, format='JPEG', quality=quality, optimize=True)

        output.seek(0)
        return output

    @classmethod
    def convert_format(
        cls,
        image_file,
        target_format: str,
        quality: int = 85
    ) -> io.BytesIO:
        """
        Convert image to a different format.

        Args:
            image_file: Image file object
            target_format: Target format (JPEG, PNG, GIF, BMP, WEBP, TIFF)
            quality: Output quality (1-100)

        Returns:
            BytesIO object containing converted image

        Example:
            converted = ImageToolsService.convert_format(
                image_file=uploaded_file,
                target_format='PNG'
            )
        """
        target_format = target_format.upper()
        if target_format not in cls.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {target_format}")

        img = Image.open(image_file)

        # Handle transparency for JPEG
        if target_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        output = io.BytesIO()

        if target_format == 'JPEG':
            img.save(output, format='JPEG', quality=quality, optimize=True)
        elif target_format == 'PNG':
            img.save(output, format='PNG', optimize=True)
        elif target_format == 'WEBP':
            img.save(output, format='WEBP', quality=quality)
        else:
            img.save(output, format=target_format)

        output.seek(0)
        return output

    @classmethod
    def crop_image(
        cls,
        image_file,
        left: int,
        top: int,
        right: int,
        bottom: int
    ) -> io.BytesIO:
        """
        Crop an image to specified coordinates.

        Args:
            image_file: Image file object
            left: Left coordinate
            top: Top coordinate
            right: Right coordinate
            bottom: Bottom coordinate

        Returns:
            BytesIO object containing cropped image

        Example:
            cropped = ImageToolsService.crop_image(
                image_file=uploaded_file,
                left=100,
                top=100,
                right=500,
                bottom=400
            )
        """
        img = Image.open(image_file)

        # Crop image
        cropped = img.crop((left, top, right, bottom))

        output = io.BytesIO()
        format = img.format or 'JPEG'

        if format == 'JPEG' and cropped.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', cropped.size, (255, 255, 255))
            rgb_img.paste(cropped, mask=cropped.split()[-1] if cropped.mode == 'RGBA' else None)
            cropped = rgb_img

        cropped.save(output, format=format, optimize=True)
        output.seek(0)
        return output

    @classmethod
    def rotate_image(
        cls,
        image_file,
        angle: float,
        expand: bool = True
    ) -> io.BytesIO:
        """
        Rotate an image by specified angle.

        Args:
            image_file: Image file object
            angle: Rotation angle in degrees (clockwise)
            expand: Expand output to fit entire rotated image

        Returns:
            BytesIO object containing rotated image

        Example:
            rotated = ImageToolsService.rotate_image(
                image_file=uploaded_file,
                angle=90
            )
        """
        img = Image.open(image_file)

        # Rotate image (PIL rotates counter-clockwise, so negate angle)
        rotated = img.rotate(-angle, expand=expand, resample=Image.Resampling.BICUBIC)

        output = io.BytesIO()
        format = img.format or 'JPEG'

        if format == 'JPEG' and rotated.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', rotated.size, (255, 255, 255))
            rgb_img.paste(rotated, mask=rotated.split()[-1] if rotated.mode == 'RGBA' else None)
            rotated = rgb_img

        rotated.save(output, format=format, optimize=True)
        output.seek(0)
        return output

    @classmethod
    def auto_orient(cls, image_file) -> io.BytesIO:
        """
        Auto-orient image based on EXIF data.

        Args:
            image_file: Image file object

        Returns:
            BytesIO object containing oriented image
        """
        img = Image.open(image_file)

        # Auto-orient using EXIF data
        img = ImageOps.exif_transpose(img)

        output = io.BytesIO()
        format = img.format or 'JPEG'

        if format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        img.save(output, format=format, optimize=True)
        output.seek(0)
        return output

    @classmethod
    def get_image_info(cls, image_file) -> dict:
        """
        Get information about an image.

        Args:
            image_file: Image file object

        Returns:
            Dict with image information

        Example:
            info = ImageToolsService.get_image_info(uploaded_file)
            # Returns: {'width': 1920, 'height': 1080, 'format': 'JPEG', ...}
        """
        img = Image.open(image_file)

        return {
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'mode': img.mode,
            'size_bytes': image_file.size if hasattr(image_file, 'size') else None,
            'has_transparency': img.mode in ('RGBA', 'LA', 'P'),
        }

    @classmethod
    def create_thumbnail(
        cls,
        image_file,
        size: Tuple[int, int] = (200, 200)
    ) -> io.BytesIO:
        """
        Create a thumbnail of an image.

        Args:
            image_file: Image file object
            size: Thumbnail size (width, height)

        Returns:
            BytesIO object containing thumbnail

        Example:
            thumbnail = ImageToolsService.create_thumbnail(
                image_file=uploaded_file,
                size=(150, 150)
            )
        """
        img = Image.open(image_file)

        # Create thumbnail (maintains aspect ratio)
        img.thumbnail(size, Image.Resampling.LANCZOS)

        output = io.BytesIO()
        format = img.format or 'JPEG'

        if format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        img.save(output, format=format, quality=85, optimize=True)
        output.seek(0)
        return output
