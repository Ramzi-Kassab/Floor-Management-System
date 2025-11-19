"""
Utility Tools API Views

REST API views for utility tools.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
import time

from floor_app.operations.utility_tools.services import (
    ImageToolsService,
    FileConversionService,
    PDFToolsService,
    TextToolsService,
    CalculatorToolsService
)
from floor_app.operations.utility_tools.models import ToolUsageLog
from .serializers import *


class BaseToolViewSet(viewsets.ViewSet):
    """Base viewset for tool operations with usage logging."""

    permission_classes = [permissions.IsAuthenticated]

    def log_tool_usage(
        self,
        user,
        tool_category: str,
        tool_type: str,
        success: bool = True,
        input_size: int = None,
        output_size: int = None,
        processing_time_ms: int = None,
        error_message: str = '',
        parameters: dict = None
    ):
        """Log tool usage for analytics."""
        try:
            ToolUsageLog.objects.create(
                user=user,
                tool_category=tool_category,
                tool_type=tool_type,
                input_size_bytes=input_size,
                output_size_bytes=output_size,
                processing_time_ms=processing_time_ms,
                success=success,
                error_message=error_message,
                parameters=parameters or {}
            )
        except Exception as e:
            # Don't fail if logging fails
            pass


class ImageToolsViewSet(BaseToolViewSet):
    """
    ViewSet for image processing tools.

    Endpoints:
    - POST /api/tools/images/resize/
    - POST /api/tools/images/compress/
    - POST /api/tools/images/convert/
    - POST /api/tools/images/crop/
    - POST /api/tools/images/rotate/
    - POST /api/tools/images/info/
    """

    @action(detail=False, methods=['post'])
    def resize(self, request):
        """
        Resize an image.

        POST /api/tools/images/resize/
        Body: multipart/form-data
            image: Image file
            width: Target width (optional)
            height: Target height (optional)
            maintain_aspect_ratio: true/false (default: true)
            quality: 1-100 (default: 85)
        """
        start_time = time.time()
        serializer = ImageResizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            # Resize image
            output = ImageToolsService.resize_image(
                image_file=data['image'],
                width=data.get('width'),
                height=data.get('height'),
                maintain_aspect_ratio=data.get('maintain_aspect_ratio', True),
                quality=data.get('quality', 85)
            )

            processing_time = int((time.time() - start_time) * 1000)

            # Log usage
            self.log_tool_usage(
                user=request.user,
                tool_category='IMAGE',
                tool_type='IMAGE_RESIZE',
                input_size=data['image'].size,
                output_size=len(output.getvalue()),
                processing_time_ms=processing_time,
                parameters={
                    'width': data.get('width'),
                    'height': data.get('height'),
                    'maintain_aspect_ratio': data.get('maintain_aspect_ratio', True),
                    'quality': data.get('quality', 85)
                }
            )

            # Return image
            response = HttpResponse(output.getvalue(), content_type='image/jpeg')
            response['Content-Disposition'] = 'attachment; filename="resized.jpg"'
            return response

        except Exception as e:
            self.log_tool_usage(
                user=request.user,
                tool_category='IMAGE',
                tool_type='IMAGE_RESIZE',
                success=False,
                error_message=str(e)
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def compress(self, request):
        """
        Compress an image.

        POST /api/tools/images/compress/
        Body: multipart/form-data
            image: Image file
            quality: 1-100 (default: 85)
            max_size_kb: Maximum size in KB (optional)
        """
        start_time = time.time()
        serializer = ImageCompressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            output = ImageToolsService.compress_image(
                image_file=data['image'],
                quality=data.get('quality', 85),
                max_size_kb=data.get('max_size_kb')
            )

            processing_time = int((time.time() - start_time) * 1000)

            self.log_tool_usage(
                user=request.user,
                tool_category='IMAGE',
                tool_type='IMAGE_COMPRESS',
                input_size=data['image'].size,
                output_size=len(output.getvalue()),
                processing_time_ms=processing_time
            )

            response = HttpResponse(output.getvalue(), content_type='image/jpeg')
            response['Content-Disposition'] = 'attachment; filename="compressed.jpg"'
            return response

        except Exception as e:
            self.log_tool_usage(
                user=request.user,
                tool_category='IMAGE',
                tool_type='IMAGE_COMPRESS',
                success=False,
                error_message=str(e)
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def convert(self, request):
        """
        Convert image format.

        POST /api/tools/images/convert/
        Body: multipart/form-data
            image: Image file
            target_format: JPEG, PNG, GIF, BMP, WEBP, TIFF
            quality: 1-100 (default: 85)
        """
        start_time = time.time()
        serializer = ImageConvertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            output = ImageToolsService.convert_format(
                image_file=data['image'],
                target_format=data['target_format'],
                quality=data.get('quality', 85)
            )

            processing_time = int((time.time() - start_time) * 1000)

            self.log_tool_usage(
                user=request.user,
                tool_category='IMAGE',
                tool_type='IMAGE_FORMAT',
                input_size=data['image'].size,
                output_size=len(output.getvalue()),
                processing_time_ms=processing_time
            )

            # Set content type based on format
            content_types = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'GIF': 'image/gif',
                'BMP': 'image/bmp',
                'WEBP': 'image/webp',
                'TIFF': 'image/tiff'
            }

            response = HttpResponse(
                output.getvalue(),
                content_type=content_types.get(data['target_format'], 'image/jpeg')
            )
            response['Content-Disposition'] = f'attachment; filename="converted.{data["target_format"].lower()}"'
            return response

        except Exception as e:
            self.log_tool_usage(
                user=request.user,
                tool_category='IMAGE',
                tool_type='IMAGE_FORMAT',
                success=False,
                error_message=str(e)
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def info(self, request):
        """
        Get image information.

        POST /api/tools/images/info/
        Body: multipart/form-data
            image: Image file
        """
        if 'image' not in request.FILES:
            return Response({'error': 'Image file required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            info = ImageToolsService.get_image_info(request.FILES['image'])
            return Response(info)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FileConversionViewSet(BaseToolViewSet):
    """
    ViewSet for file conversion tools.

    Endpoints:
    - POST /api/tools/file-conversion/excel-to-csv/
    - POST /api/tools/file-conversion/csv-to-excel/
    - POST /api/tools/file-conversion/json-to-excel/
    - POST /api/tools/file-conversion/excel-to-json/
    - POST /api/tools/file-conversion/csv-to-json/
    - POST /api/tools/file-conversion/json-to-csv/
    """

    @action(detail=False, methods=['post'])
    def excel_to_csv(self, request):
        """
        Convert Excel to CSV.

        POST /api/tools/file-conversion/excel-to-csv/
        Body: multipart/form-data
            file: Excel file
            sheet_name: Sheet name (optional)
            delimiter: Delimiter character (default: ,)
        """
        start_time = time.time()
        serializer = ExcelToCSVSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            output = FileConversionService.excel_to_csv(
                excel_file=data['file'],
                sheet_name=data.get('sheet_name'),
                delimiter=data.get('delimiter', ',')
            )

            processing_time = int((time.time() - start_time) * 1000)

            self.log_tool_usage(
                user=request.user,
                tool_category='FILE',
                tool_type='EXCEL_TO_CSV',
                input_size=data['file'].size,
                processing_time_ms=processing_time
            )

            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="converted.csv"'
            return response

        except Exception as e:
            self.log_tool_usage(
                user=request.user,
                tool_category='FILE',
                tool_type='EXCEL_TO_CSV',
                success=False,
                error_message=str(e)
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def csv_to_excel(self, request):
        """
        Convert CSV to Excel.

        POST /api/tools/file-conversion/csv-to-excel/
        """
        start_time = time.time()
        serializer = CSVToExcelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            output = FileConversionService.csv_to_excel(
                csv_file=data['file'],
                sheet_name=data.get('sheet_name', 'Sheet1'),
                has_header=data.get('has_header', True),
                delimiter=data.get('delimiter', ',')
            )

            processing_time = int((time.time() - start_time) * 1000)

            self.log_tool_usage(
                user=request.user,
                tool_category='FILE',
                tool_type='CSV_TO_EXCEL',
                input_size=data['file'].size,
                processing_time_ms=processing_time
            )

            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="converted.xlsx"'
            return response

        except Exception as e:
            self.log_tool_usage(
                user=request.user,
                tool_category='FILE',
                tool_type='CSV_TO_EXCEL',
                success=False,
                error_message=str(e)
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def json_to_excel(self, request):
        """
        Convert JSON to Excel.

        POST /api/tools/file-conversion/json-to-excel/
        Body: application/json
            json_data: JSON string or object
            sheet_name: Sheet name (default: Data)
        """
        start_time = time.time()
        serializer = JSONToExcelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            output = FileConversionService.json_to_excel(
                json_data=data['json_data'],
                sheet_name=data.get('sheet_name', 'Data')
            )

            processing_time = int((time.time() - start_time) * 1000)

            self.log_tool_usage(
                user=request.user,
                tool_category='DATA',
                tool_type='JSON_TO_CSV',
                processing_time_ms=processing_time
            )

            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="converted.xlsx"'
            return response

        except Exception as e:
            self.log_tool_usage(
                user=request.user,
                tool_category='DATA',
                tool_type='JSON_TO_CSV',
                success=False,
                error_message=str(e)
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TextToolsViewSet(BaseToolViewSet):
    """
    ViewSet for text processing tools.

    Endpoints:
    - POST /api/tools/text/change-case/
    - POST /api/tools/text/count-words/
    - POST /api/tools/text/diff/
    - POST /api/tools/text/encode-decode/
    - POST /api/tools/text/generate-hash/
    - POST /api/tools/text/find-replace/
    - POST /api/tools/text/extract-emails/
    - POST /api/tools/text/extract-urls/
    """

    @action(detail=False, methods=['post'])
    def change_case(self, request):
        """
        Change text case.

        POST /api/tools/text/change-case/
        Body: {
            "text": "Hello World",
            "case_type": "upper"
        }
        """
        serializer = TextCaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            result = TextToolsService.change_case(
                text=data['text'],
                case_type=data['case_type']
            )

            self.log_tool_usage(
                user=request.user,
                tool_category='TEXT',
                tool_type='TEXT_CASE',
                parameters={'case_type': data['case_type']}
            )

            return Response({'result': result})

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def count_words(self, request):
        """
        Count words, characters, lines, etc.

        POST /api/tools/text/count-words/
        Body: {"text": "..."}
        """
        serializer = TextCountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            counts = TextToolsService.count_words(text=data['text'])

            self.log_tool_usage(
                user=request.user,
                tool_category='TEXT',
                tool_type='TEXT_COUNT'
            )

            return Response(counts)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def generate_hash(self, request):
        """
        Generate hash of text.

        POST /api/tools/text/generate-hash/
        Body: {
            "text": "...",
            "algorithm": "sha256"
        }
        """
        serializer = TextHashSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            hash_value = TextToolsService.generate_hash(
                text=data['text'],
                algorithm=data.get('algorithm', 'sha256')
            )

            self.log_tool_usage(
                user=request.user,
                tool_category='CODE',
                tool_type='HASH_GEN',
                parameters={'algorithm': data.get('algorithm', 'sha256')}
            )

            return Response({
                'hash': hash_value,
                'algorithm': data.get('algorithm', 'sha256')
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def extract_emails(self, request):
        """Extract email addresses from text."""
        text = request.data.get('text', '')
        emails = TextToolsService.extract_emails(text)
        return Response({'emails': emails, 'count': len(emails)})

    @action(detail=False, methods=['post'])
    def extract_urls(self, request):
        """Extract URLs from text."""
        text = request.data.get('text', '')
        urls = TextToolsService.extract_urls(text)
        return Response({'urls': urls, 'count': len(urls)})


class CalculatorToolsViewSet(BaseToolViewSet):
    """
    ViewSet for calculator and converter tools.

    Endpoints:
    - POST /api/tools/calculator/date-diff/
    - POST /api/tools/calculator/add-days/
    - POST /api/tools/calculator/business-days/
    - POST /api/tools/calculator/age/
    - POST /api/tools/calculator/convert-length/
    - POST /api/tools/calculator/convert-weight/
    - POST /api/tools/calculator/convert-temperature/
    - POST /api/tools/calculator/hex-to-rgb/
    - POST /api/tools/calculator/rgb-to-hex/
    - POST /api/tools/calculator/convert-base/
    """

    @action(detail=False, methods=['post'])
    def date_diff(self, request):
        """
        Calculate date difference.

        POST /api/tools/calculator/date-diff/
        Body: {
            "date1": "2024-01-01",
            "date2": "2024-12-31",
            "unit": "days"
        }
        """
        serializer = DateDiffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            diff = CalculatorToolsService.date_diff(
                date1=str(data['date1']),
                date2=str(data['date2']),
                unit=data.get('unit', 'days')
            )

            self.log_tool_usage(
                user=request.user,
                tool_category='CALCULATOR',
                tool_type='DATE_CALC'
            )

            return Response({
                'difference': diff,
                'unit': data.get('unit', 'days')
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def age(self, request):
        """
        Calculate age from birth date.

        POST /api/tools/calculator/age/
        Body: {
            "birth_date": "1990-05-15",
            "reference_date": "2024-01-18"  // optional
        }
        """
        serializer = AgeCalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            age = CalculatorToolsService.age_calculator(
                birth_date=str(data['birth_date']),
                reference_date=str(data['reference_date']) if data.get('reference_date') else None
            )

            self.log_tool_usage(
                user=request.user,
                tool_category='CALCULATOR',
                tool_type='AGE_CALC'
            )

            return Response(age)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def convert_length(self, request):
        """
        Convert length units.

        POST /api/tools/calculator/convert-length/
        Body: {
            "value": 100,
            "from_unit": "cm",
            "to_unit": "m"
        }
        """
        serializer = LengthConversionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            result = CalculatorToolsService.convert_length(
                value=data['value'],
                from_unit=data['from_unit'],
                to_unit=data['to_unit']
            )

            self.log_tool_usage(
                user=request.user,
                tool_category='CONVERTER',
                tool_type='UNIT_LENGTH'
            )

            return Response({
                'result': result,
                'from_unit': data['from_unit'],
                'to_unit': data['to_unit']
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def hex_to_rgb(self, request):
        """Convert hex color to RGB."""
        serializer = HexToRGBSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            r, g, b = CalculatorToolsService.hex_to_rgb(request.data['hex_color'])

            self.log_tool_usage(
                user=request.user,
                tool_category='CONVERTER',
                tool_type='COLOR_CONV'
            )

            return Response({'r': r, 'g': g, 'b': b, 'rgb': f'rgb({r}, {g}, {b})'})

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def rgb_to_hex(self, request):
        """Convert RGB to hex color."""
        serializer = RGBToHexSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            hex_color = CalculatorToolsService.rgb_to_hex(
                r=data['r'],
                g=data['g'],
                b=data['b']
            )

            return Response({'hex': hex_color})

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
