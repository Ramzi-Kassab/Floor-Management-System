"""Data Extraction Service - OCR & Import Logic"""

import re
import io
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from datetime import datetime
from ..models import (
    DataExtraction, ExtractedField, FieldMapping, ImportHistory,
    DataExtractionTemplate, OCRProcessingLog, SmartFieldSuggestion
)

User = get_user_model()


class ExtractionService:
    """Service for data extraction from various sources"""

    @classmethod
    def generate_extraction_number(cls) -> str:
        """Generate unique extraction number"""
        year = timezone.now().year
        prefix = f"EXT-{year}-"
        last = DataExtraction.objects.filter(
            extraction_number__startswith=prefix
        ).order_by('-extraction_number').first()

        if last:
            last_num = int(last.extraction_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:06d}"

    @classmethod
    @transaction.atomic
    def create_extraction(cls, uploaded_by: User, source_type: str,
                         source_file, original_filename: str,
                         file_size: int, **settings) -> DataExtraction:
        """Create new data extraction job"""
        extraction = DataExtraction.objects.create(
            extraction_number=cls.generate_extraction_number(),
            uploaded_by=uploaded_by,
            source_type=source_type,
            source_file=source_file,
            original_filename=original_filename,
            file_size=file_size,
            ocr_language=settings.get('ocr_language', 'eng'),
            auto_detect_tables=settings.get('auto_detect_tables', True),
            auto_detect_headers=settings.get('auto_detect_headers', True),
        )

        # Log creation
        OCRProcessingLog.objects.create(
            extraction=extraction,
            step_name='UPLOAD',
            step_status='COMPLETED',
            details={'filename': original_filename, 'size': file_size}
        )

        return extraction

    @classmethod
    @transaction.atomic
    def process_extraction(cls, extraction: DataExtraction) -> DataExtraction:
        """Process the uploaded file and extract data"""
        extraction.status = 'PROCESSING'
        extraction.processing_started_at = timezone.now()
        extraction.save()

        try:
            if extraction.source_type == 'PHOTO':
                cls._process_photo(extraction)
            elif extraction.source_type == 'PDF':
                cls._process_pdf(extraction)
            elif extraction.source_type == 'EXCEL':
                cls._process_excel(extraction)
            elif extraction.source_type == 'CSV':
                cls._process_csv(extraction)

            extraction.status = 'EXTRACTED'
            extraction.processing_completed_at = timezone.now()
            extraction.save()

            # Auto-detect field mappings
            cls._auto_detect_field_mappings(extraction)

        except Exception as e:
            extraction.status = 'FAILED'
            extraction.import_errors = [{'error': str(e)}]
            extraction.save()

            OCRProcessingLog.objects.create(
                extraction=extraction,
                step_name='PROCESSING',
                step_status='FAILED',
                error_message=str(e)
            )

            raise

        return extraction

    @classmethod
    def _process_photo(cls, extraction: DataExtraction) -> None:
        """Extract text from photo using OCR"""
        log = OCRProcessingLog.objects.create(
            extraction=extraction,
            step_name='OCR_PHOTO',
            step_status='STARTED'
        )

        try:
            # Import PIL and pytesseract (optional dependencies)
            try:
                from PIL import Image
                import pytesseract
            except ImportError:
                # Fallback: store placeholder for manual processing
                extraction.raw_text = "[OCR libraries not installed - pytesseract/PIL required]"
                extraction.extracted_data = {
                    'note': 'Install pytesseract and Pillow for OCR support',
                    'manual_entry_required': True
                }
                log.step_status = 'COMPLETED'
                log.details = {'method': 'placeholder'}
                log.save()
                return

            # Perform OCR
            image = Image.open(extraction.source_file.path)
            text = pytesseract.image_to_string(
                image,
                lang=extraction.ocr_language
            )

            extraction.raw_text = text

            # Try to detect structured data
            structured_data = cls._extract_structured_data_from_text(text)
            extraction.extracted_data = structured_data

            # Detect tables if enabled
            if extraction.auto_detect_tables:
                tables = cls._detect_tables_in_text(text)
                extraction.detected_tables = tables
                cls._create_fields_from_tables(extraction, tables)

            log.step_status = 'COMPLETED'
            log.completed_at = timezone.now()
            log.details = {'text_length': len(text), 'tables_found': len(extraction.detected_tables)}

        except Exception as e:
            log.step_status = 'FAILED'
            log.error_message = str(e)
            raise
        finally:
            log.save()

    @classmethod
    def _process_pdf(cls, extraction: DataExtraction) -> None:
        """Extract text and tables from PDF"""
        log = OCRProcessingLog.objects.create(
            extraction=extraction,
            step_name='PDF_EXTRACTION',
            step_status='STARTED'
        )

        try:
            # Try PyPDF2 first for text-based PDFs
            try:
                import PyPDF2
            except ImportError:
                extraction.raw_text = "[PDF libraries not installed - PyPDF2 required]"
                extraction.extracted_data = {
                    'note': 'Install PyPDF2 for PDF text extraction',
                    'manual_entry_required': True
                }
                log.step_status = 'COMPLETED'
                log.details = {'method': 'placeholder'}
                log.save()
                return

            pdf_reader = PyPDF2.PdfReader(extraction.source_file.path)
            text = ''

            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'

            extraction.raw_text = text

            # If no text extracted (scanned PDF), try OCR
            if len(text.strip()) < 50:
                cls._process_scanned_pdf(extraction)
            else:
                # Extract structured data
                structured_data = cls._extract_structured_data_from_text(text)
                extraction.extracted_data = structured_data

                # Detect tables
                if extraction.auto_detect_tables:
                    tables = cls._detect_tables_in_text(text)
                    extraction.detected_tables = tables
                    cls._create_fields_from_tables(extraction, tables)

            log.step_status = 'COMPLETED'
            log.completed_at = timezone.now()
            log.details = {'text_length': len(text), 'pages': len(pdf_reader.pages)}

        except Exception as e:
            log.step_status = 'FAILED'
            log.error_message = str(e)
            raise
        finally:
            log.save()

    @classmethod
    def _process_scanned_pdf(cls, extraction: DataExtraction) -> None:
        """Process scanned PDF using OCR"""
        try:
            from pdf2image import convert_from_path
            from PIL import Image
            import pytesseract
        except ImportError:
            extraction.raw_text = "[OCR libraries not installed - pdf2image/pytesseract required]"
            return

        # Convert PDF pages to images
        images = convert_from_path(extraction.source_file.path)

        all_text = ''
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image, lang=extraction.ocr_language)
            all_text += f"\n--- Page {i+1} ---\n{text}"

        extraction.raw_text = all_text

        # Extract structured data
        structured_data = cls._extract_structured_data_from_text(all_text)
        extraction.extracted_data = structured_data

    @classmethod
    def _process_excel(cls, extraction: DataExtraction) -> None:
        """Extract data from Excel file"""
        log = OCRProcessingLog.objects.create(
            extraction=extraction,
            step_name='EXCEL_EXTRACTION',
            step_status='STARTED'
        )

        try:
            import openpyxl
        except ImportError:
            extraction.raw_text = "[Excel libraries not installed - openpyxl required]"
            extraction.extracted_data = {
                'note': 'Install openpyxl for Excel support',
                'manual_entry_required': True
            }
            log.step_status = 'COMPLETED'
            log.details = {'method': 'placeholder'}
            log.save()
            return

        try:
            wb = openpyxl.load_workbook(extraction.source_file.path)
            tables = []

            for sheet_idx, sheet in enumerate(wb.worksheets):
                # Extract all data from sheet
                data = []
                for row in sheet.iter_rows(values_only=True):
                    if any(cell is not None for cell in row):  # Skip empty rows
                        data.append([str(cell) if cell is not None else '' for cell in row])

                if data:
                    # First row as headers if auto-detect is enabled
                    headers = data[0] if extraction.auto_detect_headers else [f"Column_{i+1}" for i in range(len(data[0]))]
                    rows = data[1:] if extraction.auto_detect_headers else data

                    tables.append({
                        'sheet_name': sheet.title,
                        'sheet_index': sheet_idx,
                        'headers': headers,
                        'data': rows,
                        'total_rows': len(rows),
                        'total_columns': len(headers)
                    })

            extraction.detected_tables = tables
            extraction.total_rows_detected = sum(t['total_rows'] for t in tables)

            # Create fields from first table
            if tables:
                cls._create_fields_from_excel_table(extraction, tables[0])

            log.step_status = 'COMPLETED'
            log.completed_at = timezone.now()
            log.details = {'sheets': len(wb.worksheets), 'tables': len(tables)}

        except Exception as e:
            log.step_status = 'FAILED'
            log.error_message = str(e)
            raise
        finally:
            log.save()

    @classmethod
    def _process_csv(cls, extraction: DataExtraction) -> None:
        """Extract data from CSV file"""
        import csv

        log = OCRProcessingLog.objects.create(
            extraction=extraction,
            step_name='CSV_EXTRACTION',
            step_status='STARTED'
        )

        try:
            with open(extraction.source_file.path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                data = list(reader)

            if not data:
                raise ValueError("CSV file is empty")

            headers = data[0] if extraction.auto_detect_headers else [f"Column_{i+1}" for i in range(len(data[0]))]
            rows = data[1:] if extraction.auto_detect_headers else data

            table = {
                'headers': headers,
                'data': rows,
                'total_rows': len(rows),
                'total_columns': len(headers)
            }

            extraction.detected_tables = [table]
            extraction.total_rows_detected = len(rows)

            cls._create_fields_from_excel_table(extraction, table)

            log.step_status = 'COMPLETED'
            log.completed_at = timezone.now()
            log.details = {'total_rows': len(rows), 'total_columns': len(headers)}

        except Exception as e:
            log.step_status = 'FAILED'
            log.error_message = str(e)
            raise
        finally:
            log.save()

    @classmethod
    def _extract_structured_data_from_text(cls, text: str) -> Dict[str, Any]:
        """Extract key-value pairs from text"""
        data = {}

        # Pattern: "Key: Value" or "Key = Value"
        pattern = r'([A-Za-z\s]+)[:=]\s*(.+?)(?=\n|$)'
        matches = re.findall(pattern, text)

        for key, value in matches:
            data[key.strip()] = value.strip()

        return data

    @classmethod
    def _detect_tables_in_text(cls, text: str) -> List[Dict[str, Any]]:
        """Detect tables in plain text"""
        tables = []

        # Simple table detection: lines with multiple separators (|, \t, multiple spaces)
        lines = text.split('\n')
        current_table = []

        for line in lines:
            # Check if line looks like table row
            if '\t' in line or '|' in line or '  ' in line:
                cells = re.split(r'\t+|\|+|\s{2,}', line.strip())
                if len(cells) > 1:
                    current_table.append(cells)
            else:
                # End of table
                if len(current_table) > 1:
                    headers = current_table[0]
                    data = current_table[1:]
                    tables.append({
                        'headers': headers,
                        'data': data,
                        'total_rows': len(data),
                        'total_columns': len(headers)
                    })
                current_table = []

        # Add last table if exists
        if len(current_table) > 1:
            headers = current_table[0]
            data = current_table[1:]
            tables.append({
                'headers': headers,
                'data': data,
                'total_rows': len(data),
                'total_columns': len(headers)
            })

        return tables

    @classmethod
    def _create_fields_from_tables(cls, extraction: DataExtraction, tables: List[Dict]) -> None:
        """Create ExtractedField records from detected tables"""
        for table_idx, table in enumerate(tables):
            headers = table.get('headers', [])
            data = table.get('data', [])

            for col_idx, header in enumerate(headers):
                # Get column values
                values = [row[col_idx] if col_idx < len(row) else '' for row in data]
                non_empty_values = [v for v in values if v]

                # Detect field type
                field_type = cls._detect_field_type(non_empty_values)

                ExtractedField.objects.create(
                    extraction=extraction,
                    field_name=header.strip(),
                    field_type=field_type,
                    sample_values=non_empty_values[:5],
                    total_values=len(values),
                    null_count=len(values) - len(non_empty_values),
                    column_index=col_idx,
                    table_index=table_idx,
                    detected_as_number=field_type == 'number',
                    detected_as_date=field_type == 'date',
                    detected_as_email=field_type == 'email',
                    detected_as_phone=field_type == 'phone',
                    min_length=min(len(v) for v in non_empty_values) if non_empty_values else 0,
                    max_length=max(len(v) for v in non_empty_values) if non_empty_values else 0,
                    unique_values_count=len(set(non_empty_values))
                )

        extraction.total_fields_detected = extraction.fields.count()
        extraction.save(update_fields=['total_fields_detected'])

    @classmethod
    def _create_fields_from_excel_table(cls, extraction: DataExtraction, table: Dict) -> None:
        """Create ExtractedField records from Excel/CSV table"""
        headers = table['headers']
        data = table['data']

        for col_idx, header in enumerate(headers):
            # Get column values
            values = [row[col_idx] if col_idx < len(row) else '' for row in data]
            non_empty_values = [v for v in values if v]

            # Detect field type
            field_type = cls._detect_field_type(non_empty_values)

            ExtractedField.objects.create(
                extraction=extraction,
                field_name=str(header).strip(),
                field_type=field_type,
                sample_values=non_empty_values[:10],
                total_values=len(values),
                null_count=len(values) - len(non_empty_values),
                column_index=col_idx,
                table_index=0,
                detected_as_number=field_type == 'number',
                detected_as_date=field_type == 'date',
                detected_as_email=field_type == 'email',
                detected_as_phone=field_type == 'phone',
                min_length=min(len(str(v)) for v in non_empty_values) if non_empty_values else 0,
                max_length=max(len(str(v)) for v in non_empty_values) if non_empty_values else 0,
                unique_values_count=len(set(non_empty_values))
            )

        extraction.total_fields_detected = extraction.fields.count()
        extraction.save(update_fields=['total_fields_detected'])

    @classmethod
    def _detect_field_type(cls, values: List[str]) -> str:
        """Detect field type from sample values"""
        if not values:
            return 'text'

        # Check for numbers
        numbers = 0
        dates = 0
        emails = 0
        phones = 0

        for value in values[:20]:  # Sample first 20
            value_str = str(value).strip()

            # Number check
            try:
                float(value_str.replace(',', ''))
                numbers += 1
            except ValueError:
                pass

            # Date check
            date_patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            ]
            if any(re.match(pattern, value_str) for pattern in date_patterns):
                dates += 1

            # Email check
            if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value_str):
                emails += 1

            # Phone check
            if re.match(r'^\+?[\d\s\-\(\)]{10,}$', value_str):
                phones += 1

        total = len(values[:20])

        # Determine type based on majority
        if emails / total > 0.8:
            return 'email'
        if phones / total > 0.8:
            return 'phone'
        if dates / total > 0.8:
            return 'date'
        if numbers / total > 0.8:
            return 'number'

        return 'text'

    @classmethod
    def _auto_detect_field_mappings(cls, extraction: DataExtraction) -> None:
        """Auto-detect possible field mappings using smart matching"""
        if not extraction.target_model_name:
            return

        # Get target model
        try:
            model = apps.get_model(extraction.target_model_name)
        except LookupError:
            return

        # Get model fields
        model_fields = {
            f.name: f.get_internal_type()
            for f in model._meta.get_fields()
            if not f.many_to_many and not f.one_to_many
        }

        # Match extracted fields to model fields
        for extracted_field in extraction.fields.all():
            best_match = cls._find_best_field_match(
                extracted_field.field_name,
                extracted_field.field_type,
                model_fields
            )

            if best_match:
                field_name, confidence = best_match

                # Create suggestion
                SmartFieldSuggestion.objects.create(
                    extracted_field=extracted_field,
                    suggested_model=extraction.target_model_name,
                    suggested_field=field_name,
                    confidence=confidence,
                    reason=f"Field name similarity and type compatibility"
                )

    @classmethod
    def _find_best_field_match(cls, extracted_name: str, extracted_type: str,
                               model_fields: Dict[str, str]) -> Optional[Tuple[str, Decimal]]:
        """Find best matching model field"""
        from difflib import SequenceMatcher

        best_match = None
        best_score = 0

        extracted_name_clean = extracted_name.lower().replace('_', '').replace(' ', '')

        for field_name, field_type in model_fields.items():
            field_name_clean = field_name.lower().replace('_', '')

            # Calculate name similarity
            similarity = SequenceMatcher(None, extracted_name_clean, field_name_clean).ratio()

            # Boost score for type compatibility
            type_boost = 0
            if extracted_type == 'number' and 'Integer' in field_type or 'Decimal' in field_type:
                type_boost = 0.2
            elif extracted_type == 'date' and 'Date' in field_type:
                type_boost = 0.2
            elif extracted_type == 'email' and 'Email' in field_type:
                type_boost = 0.3
            elif extracted_type == 'text' and 'Char' in field_type or 'Text' in field_type:
                type_boost = 0.1

            total_score = similarity + type_boost

            if total_score > best_score and total_score > 0.5:  # Minimum 50% match
                best_score = total_score
                best_match = (field_name, Decimal(str(round(total_score * 100, 2))))

        return best_match

    @classmethod
    @transaction.atomic
    def create_field_mapping(cls, extraction: DataExtraction, extracted_field_id: int,
                            target_model: str, target_field: str,
                            mapping_type: str = 'DIRECT', **config) -> FieldMapping:
        """Create a field mapping"""
        extracted_field = ExtractedField.objects.get(id=extracted_field_id)

        # Get target field type
        model = apps.get_model(target_model)
        field = model._meta.get_field(target_field)

        mapping = FieldMapping.objects.create(
            extraction=extraction,
            extracted_field=extracted_field,
            target_model=target_model,
            target_field=target_field,
            target_field_type=field.get_internal_type(),
            mapping_type=mapping_type,
            transformation_rule=config.get('transformation_rule', {}),
            default_value=config.get('default_value', ''),
            is_required=config.get('is_required', False),
            validation_rule=config.get('validation_rule', {})
        )

        extraction.status = 'MAPPED'
        extraction.save(update_fields=['status'])

        return mapping

    @classmethod
    @transaction.atomic
    def execute_import(cls, extraction: DataExtraction) -> DataExtraction:
        """Execute the data import based on mappings"""
        if extraction.status != 'MAPPED':
            raise ValueError("Extraction must be in MAPPED status to import")

        log = OCRProcessingLog.objects.create(
            extraction=extraction,
            step_name='IMPORT',
            step_status='STARTED'
        )

        try:
            # Get mappings
            mappings = extraction.mappings.all()
            if not mappings.exists():
                raise ValueError("No field mappings configured")

            # Get target model
            target_model = apps.get_model(mappings.first().target_model)
            target_content_type = ContentType.objects.get_for_model(target_model)

            # Get data from first table
            if not extraction.detected_tables:
                raise ValueError("No tables detected to import")

            table = extraction.detected_tables[0]
            rows = table['data']

            success_count = 0
            fail_count = 0

            for row_idx, row in enumerate(rows):
                try:
                    # Build object data from mappings
                    object_data = {}

                    for mapping in mappings:
                        if mapping.mapping_type == 'SKIP':
                            continue

                        col_idx = mapping.extracted_field.column_index
                        value = row[col_idx] if col_idx < len(row) else ''

                        # Transform value
                        transformed_value = cls._transform_value(
                            value,
                            mapping.target_field_type,
                            mapping.transformation_rule
                        )

                        object_data[mapping.target_field] = transformed_value

                    # Create object
                    obj = target_model.objects.create(**object_data)

                    # Record success
                    ImportHistory.objects.create(
                        extraction=extraction,
                        row_index=row_idx,
                        source_data=dict(zip([f.field_name for f in extraction.fields.all()], row)),
                        target_content_type=target_content_type,
                        target_object_id=obj.pk,
                        import_status='SUCCESS',
                        transformed_data=object_data
                    )

                    success_count += 1

                except Exception as e:
                    # Record failure
                    ImportHistory.objects.create(
                        extraction=extraction,
                        row_index=row_idx,
                        source_data=dict(zip([f.field_name for f in extraction.fields.all()], row)),
                        target_content_type=target_content_type,
                        import_status='FAILED',
                        error_message=str(e)
                    )

                    fail_count += 1

            extraction.total_imported = success_count
            extraction.total_failed = fail_count
            extraction.status = 'IMPORTED'
            extraction.save()

            log.step_status = 'COMPLETED'
            log.completed_at = timezone.now()
            log.details = {'success': success_count, 'failed': fail_count}

        except Exception as e:
            log.step_status = 'FAILED'
            log.error_message = str(e)
            raise
        finally:
            log.save()

        return extraction

    @classmethod
    def _transform_value(cls, value: str, target_type: str, transformation_rule: Dict) -> Any:
        """Transform value based on target type and rules"""
        if not value or value.strip() == '':
            return None

        try:
            # Apply transformation rules first
            if transformation_rule:
                # Handle custom transformations
                if transformation_rule.get('type') == 'LOOKUP':
                    lookup_table = transformation_rule.get('lookup_table', {})
                    value = lookup_table.get(value, value)
                elif transformation_rule.get('type') == 'REGEX':
                    pattern = transformation_rule.get('pattern')
                    replacement = transformation_rule.get('replacement', '')
                    value = re.sub(pattern, replacement, value)

            # Convert to target type
            if 'Integer' in target_type:
                return int(float(str(value).replace(',', '')))
            elif 'Decimal' in target_type or 'Float' in target_type:
                return Decimal(str(value).replace(',', ''))
            elif 'Boolean' in target_type:
                return value.lower() in ['true', 'yes', '1', 'y']
            elif 'Date' in target_type:
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
                return value  # Return as string if can't parse
            else:
                return str(value)

        except Exception:
            return value  # Return original on error

    @classmethod
    def get_extraction_statistics(cls, extraction: DataExtraction) -> Dict[str, Any]:
        """Get detailed statistics for extraction"""
        return {
            'extraction_number': extraction.extraction_number,
            'status': extraction.status,
            'source_type': extraction.get_source_type_display(),
            'total_fields_detected': extraction.total_fields_detected,
            'total_rows_detected': extraction.total_rows_detected,
            'total_tables': len(extraction.detected_tables),
            'total_imported': extraction.total_imported,
            'total_failed': extraction.total_failed,
            'success_rate': (extraction.total_imported / (extraction.total_imported + extraction.total_failed) * 100)
                           if (extraction.total_imported + extraction.total_failed) > 0 else 0,
            'processing_duration': (
                (extraction.processing_completed_at - extraction.processing_started_at).total_seconds()
                if extraction.processing_completed_at and extraction.processing_started_at else None
            ),
        }
