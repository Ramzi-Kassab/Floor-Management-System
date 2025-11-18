"""
Utility Tools API Serializers

Serializers for utility tools REST API.
"""

from rest_framework import serializers


# ==================== Image Tools Serializers ====================

class ImageResizeSerializer(serializers.Serializer):
    """Serializer for image resize operation."""

    image = serializers.ImageField()
    width = serializers.IntegerField(required=False, min_value=1, max_value=10000)
    height = serializers.IntegerField(required=False, min_value=1, max_value=10000)
    maintain_aspect_ratio = serializers.BooleanField(default=True)
    quality = serializers.IntegerField(default=85, min_value=1, max_value=100)


class ImageCompressSerializer(serializers.Serializer):
    """Serializer for image compress operation."""

    image = serializers.ImageField()
    quality = serializers.IntegerField(default=85, min_value=1, max_value=100)
    max_size_kb = serializers.IntegerField(required=False, min_value=1)


class ImageConvertSerializer(serializers.Serializer):
    """Serializer for image format conversion."""

    image = serializers.ImageField()
    target_format = serializers.ChoiceField(
        choices=['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP', 'TIFF']
    )
    quality = serializers.IntegerField(default=85, min_value=1, max_value=100)


class ImageCropSerializer(serializers.Serializer):
    """Serializer for image crop operation."""

    image = serializers.ImageField()
    left = serializers.IntegerField(min_value=0)
    top = serializers.IntegerField(min_value=0)
    right = serializers.IntegerField(min_value=1)
    bottom = serializers.IntegerField(min_value=1)


class ImageRotateSerializer(serializers.Serializer):
    """Serializer for image rotate operation."""

    image = serializers.ImageField()
    angle = serializers.FloatField()
    expand = serializers.BooleanField(default=True)


# ==================== File Conversion Serializers ====================

class ExcelToCSVSerializer(serializers.Serializer):
    """Serializer for Excel to CSV conversion."""

    file = serializers.FileField()
    sheet_name = serializers.CharField(required=False, allow_blank=True)
    delimiter = serializers.CharField(default=',', max_length=1)


class CSVToExcelSerializer(serializers.Serializer):
    """Serializer for CSV to Excel conversion."""

    file = serializers.FileField()
    sheet_name = serializers.CharField(default='Sheet1', max_length=100)
    has_header = serializers.BooleanField(default=True)
    delimiter = serializers.CharField(default=',', max_length=1)


class JSONToExcelSerializer(serializers.Serializer):
    """Serializer for JSON to Excel conversion."""

    json_data = serializers.CharField()
    sheet_name = serializers.CharField(default='Data', max_length=100)


class ExcelToJSONSerializer(serializers.Serializer):
    """Serializer for Excel to JSON conversion."""

    file = serializers.FileField()
    sheet_name = serializers.CharField(required=False, allow_blank=True)


# ==================== PDF Tools Serializers ====================

class PDFMergeSerializer(serializers.Serializer):
    """Serializer for PDF merge operation."""

    files = serializers.ListField(
        child=serializers.FileField(),
        min_length=2,
        max_length=100
    )


class PDFSplitSerializer(serializers.Serializer):
    """Serializer for PDF split operation."""

    file = serializers.FileField()
    pages = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False
    )
    ranges = serializers.ListField(
        child=serializers.ListField(
            child=serializers.IntegerField(min_value=1),
            min_length=2,
            max_length=2
        ),
        required=False
    )


class PDFRotateSerializer(serializers.Serializer):
    """Serializer for PDF rotate operation."""

    file = serializers.FileField()
    angle = serializers.ChoiceField(choices=[90, 180, 270, -90, -180, -270])
    pages = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False
    )


class ImagesToPDFSerializer(serializers.Serializer):
    """Serializer for images to PDF conversion."""

    files = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=100
    )
    quality = serializers.IntegerField(default=85, min_value=1, max_value=100)


# ==================== Text Tools Serializers ====================

class TextCaseSerializer(serializers.Serializer):
    """Serializer for text case conversion."""

    text = serializers.CharField()
    case_type = serializers.ChoiceField(
        choices=['upper', 'lower', 'title', 'sentence', 'camel', 'pascal', 'snake', 'kebab']
    )


class TextCountSerializer(serializers.Serializer):
    """Serializer for text count operation."""

    text = serializers.CharField()


class TextDiffSerializer(serializers.Serializer):
    """Serializer for text diff operation."""

    text1 = serializers.CharField()
    text2 = serializers.CharField()
    output_format = serializers.ChoiceField(
        choices=['unified', 'context', 'html'],
        default='unified'
    )


class TextEncodeDecodeSerializer(serializers.Serializer):
    """Serializer for text encode/decode operation."""

    text = serializers.CharField()
    operation = serializers.ChoiceField(
        choices=[
            'base64_encode', 'base64_decode',
            'url_encode', 'url_decode',
            'html_escape', 'html_unescape'
        ]
    )
    encoding = serializers.CharField(default='utf-8')


class TextHashSerializer(serializers.Serializer):
    """Serializer for text hash generation."""

    text = serializers.CharField()
    algorithm = serializers.ChoiceField(
        choices=['md5', 'sha1', 'sha256', 'sha512'],
        default='sha256'
    )


class TextFindReplaceSerializer(serializers.Serializer):
    """Serializer for find and replace operation."""

    text = serializers.CharField()
    find = serializers.CharField()
    replace = serializers.CharField()
    case_sensitive = serializers.BooleanField(default=True)
    whole_word = serializers.BooleanField(default=False)


# ==================== Calculator Serializers ====================

class DateDiffSerializer(serializers.Serializer):
    """Serializer for date difference calculation."""

    date1 = serializers.DateField()
    date2 = serializers.DateField()
    unit = serializers.ChoiceField(
        choices=['days', 'weeks', 'months', 'years'],
        default='days'
    )


class AddDaysSerializer(serializers.Serializer):
    """Serializer for add days operation."""

    date = serializers.DateField()
    days = serializers.IntegerField()


class BusinessDaysSerializer(serializers.Serializer):
    """Serializer for business days calculation."""

    date1 = serializers.DateField()
    date2 = serializers.DateField()
    holidays = serializers.ListField(
        child=serializers.DateField(),
        required=False
    )


class AgeCalculatorSerializer(serializers.Serializer):
    """Serializer for age calculation."""

    birth_date = serializers.DateField()
    reference_date = serializers.DateField(required=False)


class LengthConversionSerializer(serializers.Serializer):
    """Serializer for length conversion."""

    value = serializers.FloatField()
    from_unit = serializers.ChoiceField(
        choices=['mm', 'cm', 'm', 'km', 'in', 'ft', 'yd', 'mi']
    )
    to_unit = serializers.ChoiceField(
        choices=['mm', 'cm', 'm', 'km', 'in', 'ft', 'yd', 'mi']
    )


class WeightConversionSerializer(serializers.Serializer):
    """Serializer for weight conversion."""

    value = serializers.FloatField()
    from_unit = serializers.ChoiceField(
        choices=['mg', 'g', 'kg', 'ton', 'oz', 'lb']
    )
    to_unit = serializers.ChoiceField(
        choices=['mg', 'g', 'kg', 'ton', 'oz', 'lb']
    )


class TemperatureConversionSerializer(serializers.Serializer):
    """Serializer for temperature conversion."""

    value = serializers.FloatField()
    from_unit = serializers.ChoiceField(choices=['C', 'F', 'K'])
    to_unit = serializers.ChoiceField(choices=['C', 'F', 'K'])


class HexToRGBSerializer(serializers.Serializer):
    """Serializer for hex to RGB conversion."""

    hex_color = serializers.RegexField(regex=r'^#?[0-9A-Fa-f]{6}$')


class RGBToHexSerializer(serializers.Serializer):
    """Serializer for RGB to hex conversion."""

    r = serializers.IntegerField(min_value=0, max_value=255)
    g = serializers.IntegerField(min_value=0, max_value=255)
    b = serializers.IntegerField(min_value=0, max_value=255)


class BaseConversionSerializer(serializers.Serializer):
    """Serializer for number base conversion."""

    number = serializers.CharField()
    from_base = serializers.IntegerField(min_value=2, max_value=36)
    to_base = serializers.IntegerField(min_value=2, max_value=36)
