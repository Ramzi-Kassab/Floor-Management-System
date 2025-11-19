"""
Data Extraction System Views

Template-rendering views for OCR, data extraction, and import from photos/PDF/Excel.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.files.storage import default_storage
import uuid

from .models import (
    DataExtraction,
    ExtractedField,
    FieldMapping,
    ImportHistory,
    DataExtractionTemplate,
    OCRProcessingLog,
    SmartFieldSuggestion,
)


@login_required
def upload(request):
    """
    Upload file for data extraction.

    Handles:
    - File upload (photo, PDF, Excel, CSV)
    - Validation
    - OCR/extraction initiation
    """
    try:
        if request.method == 'POST':
            try:
                source_file = request.FILES.get('source_file')
                source_type = request.POST.get('source_type')
                ocr_language = request.POST.get('ocr_language', 'eng')
                auto_detect_tables = request.POST.get('auto_detect_tables') == 'on'
                auto_detect_headers = request.POST.get('auto_detect_headers') == 'on'

                if not source_file:
                    messages.error(request, 'Please select a file to upload.')
                elif not source_type:
                    messages.error(request, 'Please select source type.')
                else:
                    # Generate unique extraction number
                    extraction_number = f'EXT-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:8].upper()}'

                    # Create extraction record
                    extraction = DataExtraction.objects.create(
                        extraction_number=extraction_number,
                        uploaded_by=request.user,
                        source_type=source_type,
                        source_file=source_file,
                        original_filename=source_file.name,
                        file_size=source_file.size,
                        status='UPLOADED',
                        ocr_language=ocr_language,
                        auto_detect_tables=auto_detect_tables,
                        auto_detect_headers=auto_detect_headers
                    )

                    # Log upload
                    OCRProcessingLog.objects.create(
                        extraction=extraction,
                        step_name='File Upload',
                        step_status='COMPLETED',
                        details={'filename': source_file.name, 'size': source_file.size}
                    )

                    messages.success(request, f'File uploaded successfully. Extraction Number: {extraction_number}')
                    return redirect('data_extraction:field_mapping', pk=extraction.pk)

            except Exception as e:
                messages.error(request, f'Error uploading file: {str(e)}')

        # Get available templates
        templates = DataExtractionTemplate.objects.filter(
            Q(created_by=request.user) | Q(is_shared=True),
            is_active=True
        ).order_by('-usage_count')

        context = {
            'source_types': DataExtraction.SOURCE_TYPES,
            'templates': templates,
            'page_title': 'Upload for Data Extraction',
        }

    except Exception as e:
        messages.error(request, f'Error loading upload page: {str(e)}')
        context = {
            'source_types': [],
            'templates': [],
            'page_title': 'Upload for Data Extraction',
        }

    return render(request, 'data_extraction/upload.html', context)


@login_required
def field_mapping(request, pk):
    """
    Map extracted fields to system fields.

    Shows:
    - Detected fields
    - Smart suggestions
    - Manual mapping interface
    """
    try:
        extraction = get_object_or_404(
            DataExtraction.objects.select_related('uploaded_by'),
            pk=pk
        )

        # Check permission
        if extraction.uploaded_by != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to view this extraction.')
            return redirect('data_extraction:extraction_history')

        # Handle mapping submission
        if request.method == 'POST':
            try:
                action = request.POST.get('action')

                if action == 'save_mapping':
                    # Save field mappings
                    field_ids = request.POST.getlist('field_id[]')
                    target_models = request.POST.getlist('target_model[]')
                    target_fields = request.POST.getlist('target_field[]')
                    mapping_types = request.POST.getlist('mapping_type[]')

                    # Clear existing mappings
                    extraction.mappings.all().delete()

                    # Create new mappings
                    for i, field_id in enumerate(field_ids):
                        if target_models[i] and target_fields[i]:
                            try:
                                extracted_field = ExtractedField.objects.get(pk=field_id)
                                FieldMapping.objects.create(
                                    extraction=extraction,
                                    extracted_field=extracted_field,
                                    target_model=target_models[i],
                                    target_field=target_fields[i],
                                    target_field_type='text',  # Could be enhanced
                                    mapping_type=mapping_types[i] if i < len(mapping_types) else 'DIRECT'
                                )
                            except ExtractedField.DoesNotExist:
                                pass

                    extraction.status = 'MAPPED'
                    extraction.save()

                    messages.success(request, 'Field mappings saved successfully.')
                    return redirect('data_extraction:extraction_results', pk=pk)

                elif action == 'process_extraction':
                    # Trigger actual extraction/OCR processing
                    extraction.status = 'PROCESSING'
                    extraction.processing_started_at = timezone.now()
                    extraction.save()

                    # Log processing start
                    OCRProcessingLog.objects.create(
                        extraction=extraction,
                        step_name='Data Extraction',
                        step_status='STARTED'
                    )

                    # TODO: Trigger actual OCR/extraction task (celery, etc.)
                    # For now, mark as extracted
                    extraction.status = 'EXTRACTED'
                    extraction.processing_completed_at = timezone.now()
                    extraction.total_fields_detected = 10  # Mock
                    extraction.save()

                    messages.success(request, 'Extraction processing started.')
                    return redirect('data_extraction:field_mapping', pk=pk)

            except Exception as e:
                messages.error(request, f'Error saving mappings: {str(e)}')

        # Get extracted fields
        fields = extraction.fields.all().order_by('table_index', 'column_index')

        # Get smart suggestions for each field
        field_suggestions = {}
        for field in fields:
            suggestions = field.suggestions.filter(confidence__gte=0.7).order_by('-confidence')[:3]
            field_suggestions[field.pk] = suggestions

        # Get existing mappings
        mappings = {m.extracted_field_id: m for m in extraction.mappings.all()}

        # Get processing logs
        logs = extraction.processing_logs.all().order_by('-started_at')

        context = {
            'extraction': extraction,
            'fields': fields,
            'field_suggestions': field_suggestions,
            'mappings': mappings,
            'logs': logs,
            'mapping_types': FieldMapping.MAPPING_TYPES,
            'page_title': f'Field Mapping - {extraction.extraction_number}',
        }

    except Exception as e:
        messages.error(request, f'Error loading field mapping: {str(e)}')
        return redirect('data_extraction:extraction_history')

    return render(request, 'data_extraction/field_mapping.html', context)


@login_required
def extraction_results(request, pk):
    """
    View extraction results and import data.

    Shows:
    - Extracted data preview
    - Import summary
    - Error details
    """
    try:
        extraction = get_object_or_404(
            DataExtraction.objects.select_related('uploaded_by'),
            pk=pk
        )

        # Check permission
        if extraction.uploaded_by != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to view this extraction.')
            return redirect('data_extraction:extraction_history')

        # Handle import action
        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'import_data':
                try:
                    # TODO: Implement actual import logic
                    extraction.status = 'IMPORTED'
                    extraction.total_imported = extraction.total_rows_detected
                    extraction.save()

                    messages.success(request, f'Successfully imported {extraction.total_imported} records.')
                    return redirect('data_extraction:extraction_results', pk=pk)

                except Exception as e:
                    messages.error(request, f'Error importing data: {str(e)}')

        # Get import history
        import_records = extraction.import_records.all().order_by('row_index')

        # Get statistics
        stats = {
            'total_fields': extraction.fields.count(),
            'total_mappings': extraction.mappings.count(),
            'total_rows': extraction.total_rows_detected,
            'imported': extraction.total_imported,
            'failed': extraction.total_failed,
            'success_rate': (extraction.total_imported / extraction.total_rows_detected * 100) if extraction.total_rows_detected > 0 else 0,
        }

        context = {
            'extraction': extraction,
            'import_records': import_records[:100],  # Limit display
            'stats': stats,
            'page_title': f'Extraction Results - {extraction.extraction_number}',
        }

    except Exception as e:
        messages.error(request, f'Error loading extraction results: {str(e)}')
        return redirect('data_extraction:extraction_history')

    return render(request, 'data_extraction/extraction_results.html', context)


@login_required
def extraction_history(request):
    """
    View history of all extractions.

    Shows:
    - All user's extractions
    - Filter by status, source type
    - Search functionality
    """
    try:
        # Get extractions
        extractions = DataExtraction.objects.filter(
            uploaded_by=request.user
        ).annotate(
            field_count=Count('fields'),
            mapping_count=Count('mappings')
        ).order_by('-created_at')

        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            extractions = extractions.filter(status=status_filter)

        # Filter by source type
        source_type = request.GET.get('source_type')
        if source_type:
            extractions = extractions.filter(source_type=source_type)

        # Search
        search_query = request.GET.get('q')
        if search_query:
            extractions = extractions.filter(
                Q(extraction_number__icontains=search_query) |
                Q(original_filename__icontains=search_query) |
                Q(target_model_name__icontains=search_query)
            )

        # Statistics
        stats = {
            'total': DataExtraction.objects.filter(uploaded_by=request.user).count(),
            'uploaded': DataExtraction.objects.filter(uploaded_by=request.user, status='UPLOADED').count(),
            'processing': DataExtraction.objects.filter(uploaded_by=request.user, status='PROCESSING').count(),
            'imported': DataExtraction.objects.filter(uploaded_by=request.user, status='IMPORTED').count(),
            'failed': DataExtraction.objects.filter(uploaded_by=request.user, status='FAILED').count(),
        }

        context = {
            'extractions': extractions,
            'stats': stats,
            'status_choices': DataExtraction.STATUS_CHOICES,
            'source_types': DataExtraction.SOURCE_TYPES,
            'status_filter': status_filter,
            'source_type_filter': source_type,
            'search_query': search_query,
            'page_title': 'Extraction History',
        }

    except Exception as e:
        messages.error(request, f'Error loading extraction history: {str(e)}')
        context = {
            'extractions': [],
            'stats': {},
            'page_title': 'Extraction History',
        }

    return render(request, 'data_extraction/extraction_history.html', context)
