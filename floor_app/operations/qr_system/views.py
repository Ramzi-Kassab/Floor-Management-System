"""
QR Code System Views

Template-rendering views for QR code generation, scanning, and management.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
import base64

from .models import (
    QRCode,
    QRScanLog,
    QRBatch,
)


@login_required
def generate(request):
    """
    Generate new QR codes.

    Handles:
    - Single QR code generation
    - Batch generation
    - Custom data and settings
    """
    try:
        if request.method == 'POST':
            try:
                qr_type = request.POST.get('qr_type')
                data = request.POST.get('data', '')
                label = request.POST.get('label', '')
                batch_size = request.POST.get('batch_size', '1')

                if not qr_type:
                    messages.error(request, 'Please select QR code type.')
                elif not data and qr_type != 'BATCH':
                    messages.error(request, 'Please enter data for QR code.')
                else:
                    batch_size = int(batch_size)

                    if batch_size == 1:
                        # Single QR code
                        qr_code = QRCode.objects.create(
                            qr_type=qr_type,
                            data=data,
                            label=label,
                            created_by=request.user,
                            qr_code=f'QR-{uuid.uuid4().hex[:12].upper()}'
                        )

                        messages.success(request, f'QR code generated: {qr_code.qr_code}')
                        return redirect('qr_system:qr_detail', pk=qr_code.pk)
                    else:
                        # Batch generation
                        batch = QRBatch.objects.create(
                            batch_name=label or f'Batch {timezone.now().strftime("%Y%m%d-%H%M")}',
                            qr_type=qr_type,
                            created_by=request.user,
                            total_codes=batch_size
                        )

                        # Generate codes
                        for i in range(batch_size):
                            QRCode.objects.create(
                                qr_type=qr_type,
                                data=f'{data}-{i+1}' if data else f'{batch.batch_name}-{i+1}',
                                label=f'{label} #{i+1}' if label else f'Code #{i+1}',
                                created_by=request.user,
                                batch=batch,
                                qr_code=f'QR-{uuid.uuid4().hex[:12].upper()}'
                            )

                        batch.generated_codes = batch_size
                        batch.save()

                        messages.success(request, f'Batch of {batch_size} QR codes generated.')
                        return redirect('qr_system:qr_list')

            except Exception as e:
                messages.error(request, f'Error generating QR code: {str(e)}')

        context = {
            'qr_types': QRCode.QR_TYPES,
            'page_title': 'Generate QR Codes',
        }

    except Exception as e:
        messages.error(request, f'Error loading generator: {str(e)}')
        context = {
            'qr_types': [],
            'page_title': 'Generate QR Codes',
        }

    return render(request, 'qr_system/generate.html', context)


@login_required
def qr_list(request):
    """
    List all QR codes.

    Shows:
    - All generated QR codes
    - Filter by type, status
    - Search functionality
    """
    try:
        # Get QR codes
        qr_codes = QRCode.objects.select_related(
            'created_by',
            'batch'
        ).annotate(
            scan_count=Count('scans')
        ).order_by('-created_at')

        # Filter by type
        qr_type = request.GET.get('type')
        if qr_type:
            qr_codes = qr_codes.filter(qr_type=qr_type)

        # Filter by status
        is_active = request.GET.get('active')
        if is_active == 'true':
            qr_codes = qr_codes.filter(is_active=True)
        elif is_active == 'false':
            qr_codes = qr_codes.filter(is_active=False)

        # Search
        search_query = request.GET.get('q')
        if search_query:
            qr_codes = qr_codes.filter(
                Q(qr_code__icontains=search_query) |
                Q(label__icontains=search_query) |
                Q(data__icontains=search_query)
            )

        # Statistics
        stats = {
            'total': QRCode.objects.count(),
            'active': QRCode.objects.filter(is_active=True).count(),
            'scanned_today': QRScanLog.objects.filter(scanned_at__date=timezone.now().date()).count(),
            'total_scans': QRScanLog.objects.count(),
        }

        context = {
            'qr_codes': qr_codes,
            'stats': stats,
            'qr_types': QRCode.QR_TYPES,
            'qr_type_filter': qr_type,
            'is_active_filter': is_active,
            'search_query': search_query,
            'page_title': 'QR Code List',
        }

    except Exception as e:
        messages.error(request, f'Error loading QR codes: {str(e)}')
        context = {
            'qr_codes': [],
            'stats': {},
            'page_title': 'QR Code List',
        }

    return render(request, 'qr_system/qr_list.html', context)


@login_required
def qr_detail(request, pk):
    """
    View QR code details.

    Shows:
    - QR code image
    - Scan history
    - Statistics
    - Actions (activate/deactivate, delete)
    """
    try:
        qr_code = get_object_or_404(
            QRCode.objects.select_related('created_by', 'batch'),
            pk=pk
        )

        # Handle actions
        if request.method == 'POST':
            action = request.POST.get('action')

            try:
                if action == 'activate':
                    qr_code.is_active = True
                    qr_code.save()
                    messages.success(request, 'QR code activated.')

                elif action == 'deactivate':
                    qr_code.is_active = False
                    qr_code.save()
                    messages.success(request, 'QR code deactivated.')

                elif action == 'delete':
                    qr_code.delete()
                    messages.success(request, 'QR code deleted.')
                    return redirect('qr_system:qr_list')

                return redirect('qr_system:qr_detail', pk=pk)

            except Exception as e:
                messages.error(request, f'Error performing action: {str(e)}')

        # Get scan history
        scans = qr_code.scans.select_related('scanned_by').order_by('-scanned_at')[:50]

        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code.qr_code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        # Statistics
        stats = {
            'total_scans': scans.count(),
            'unique_scanners': qr_code.scans.values('scanned_by').distinct().count(),
            'first_scan': qr_code.first_scanned_at,
            'last_scan': qr_code.last_scanned_at,
        }

        context = {
            'qr_code': qr_code,
            'scans': scans,
            'stats': stats,
            'qr_image': img_str,
            'page_title': f'QR Code - {qr_code.qr_code}',
        }

    except Exception as e:
        messages.error(request, f'Error loading QR code: {str(e)}')
        return redirect('qr_system:qr_list')

    return render(request, 'qr_system/qr_detail.html', context)


@login_required
def scan_history(request):
    """
    View scan history.

    Shows:
    - All scans
    - Filter by QR code, user, date
    """
    try:
        scans = QRScanLog.objects.select_related(
            'qr_code',
            'scanned_by'
        ).order_by('-scanned_at')

        # Filter by QR code
        qr_code_id = request.GET.get('qr_code')
        if qr_code_id:
            scans = scans.filter(qr_code_id=qr_code_id)

        # Filter by user
        user_id = request.GET.get('user')
        if user_id:
            scans = scans.filter(scanned_by_id=user_id)

        # Filter by date range
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        if from_date:
            scans = scans.filter(scanned_at__date__gte=from_date)
        if to_date:
            scans = scans.filter(scanned_at__date__lte=to_date)

        # Limit results
        scans = scans[:200]

        # Statistics
        stats = {
            'total_scans': QRScanLog.objects.count(),
            'today': QRScanLog.objects.filter(scanned_at__date=timezone.now().date()).count(),
            'this_week': QRScanLog.objects.filter(scanned_at__gte=timezone.now() - timezone.timedelta(days=7)).count(),
        }

        context = {
            'scans': scans,
            'stats': stats,
            'page_title': 'Scan History',
        }

    except Exception as e:
        messages.error(request, f'Error loading scan history: {str(e)}')
        context = {
            'scans': [],
            'stats': {},
            'page_title': 'Scan History',
        }

    return render(request, 'qr_system/scan_history.html', context)


@login_required
def integration_guide(request):
    """
    Show integration guide for QR system.

    Provides:
    - API documentation
    - Code examples
    - Integration steps
    """
    context = {
        'page_title': 'QR System Integration Guide',
    }

    return render(request, 'qr_system/integration_guide.html', context)
