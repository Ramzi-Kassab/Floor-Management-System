"""
Employee Document Management Views
Clear separation between Employee Self-Service and HR Administration
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from django.http import JsonResponse, FileResponse, HttpResponse
from datetime import timedelta
import os

from floor_app.operations.hr.models import (
    EmployeeDocument, DocumentRenewal, ExpiryAlert,
    DocumentType, DocumentStatus, HREmployee
)
from floor_app.operations.hr.forms.document_forms import (
    EmployeeDocumentUploadForm, DocumentRenewalRequestForm,
    HRDocumentForm, DocumentSearchForm, DocumentVerificationForm,
    BulkDocumentActionForm, ExpiryAlertForm
)


def is_staff(user):
    """Check if user is staff"""
    return user.is_staff


# ============================================================================
# EMPLOYEE VIEWS (Self-Service Portal)
# ============================================================================

@login_required
def my_documents_dashboard(request):
    """
    Employee's personal document dashboard
    Simple, focused on their own documents
    """
    try:
        employee = request.user.hremployee
    except:
        messages.error(request, 'Employee record not found.')
        return redirect('hr:dashboard')

    # Get employee's documents
    documents = EmployeeDocument.objects.filter(
        employee=employee,
        is_deleted=False
    ).order_by('-created_at')

    # Get document counts by type
    doc_counts = documents.values('document_type').annotate(count=Count('id'))

    # Get expiring documents
    today = timezone.now().date()
    expiring_soon = documents.filter(
        expiry_date__isnull=False,
        expiry_date__lte=today + timedelta(days=30),
        expiry_date__gte=today
    ).order_by('expiry_date')

    # Get expired documents
    expired = documents.filter(
        expiry_date__isnull=False,
        expiry_date__lt=today
    )

    # Get recent uploads
    recent_uploads = documents[:5]

    # Get pending renewals
    pending_renewals = DocumentRenewal.objects.filter(
        document__employee=employee,
        status='REQUESTED'
    ).select_related('document')

    context = {
        'employee': employee,
        'documents': documents,
        'doc_counts': doc_counts,
        'total_documents': documents.count(),
        'expiring_soon': expiring_soon,
        'expiring_count': expiring_soon.count(),
        'expired': expired,
        'expired_count': expired.count(),
        'recent_uploads': recent_uploads,
        'pending_renewals': pending_renewals,
    }

    return render(request, 'hr/documents/employee/my_documents.html', context)


@login_required
def employee_upload_document(request):
    """
    Simple upload form for employees
    """
    try:
        employee = request.user.hremployee
    except:
        messages.error(request, 'Employee record not found.')
        return redirect('hr:dashboard')

    if request.method == 'POST':
        form = EmployeeDocumentUploadForm(request.POST, request.FILES, employee=employee)
        if form.is_valid():
            document = form.save()

            # Handle actual file save (this would integrate with your file storage)
            file = request.FILES['file']
            # Save file to storage here...

            messages.success(
                request,
                f'Document "{document.title}" uploaded successfully! HR will review it shortly.'
            )
            return redirect('hr:my_documents')
    else:
        form = EmployeeDocumentUploadForm(employee=employee)

    return render(request, 'hr/documents/employee/upload_document.html', {
        'form': form,
        'employee': employee,
    })


@login_required
def employee_view_document(request, pk):
    """
    View document details (employee can only see their own)
    """
    try:
        employee = request.user.hremployee
    except:
        messages.error(request, 'Employee record not found.')
        return redirect('hr:dashboard')

    document = get_object_or_404(
        EmployeeDocument,
        pk=pk,
        employee=employee,
        is_deleted=False
    )

    # Get renewal history
    renewals = document.renewals.all().order_by('-request_date')

    context = {
        'document': document,
        'renewals': renewals,
        'can_request_renewal': document.expiry_date and document.days_until_expiry and document.days_until_expiry <= 90,
    }

    return render(request, 'hr/documents/employee/view_document.html', context)


@login_required
def employee_request_renewal(request, pk):
    """
    Employee requests document renewal
    """
    try:
        employee = request.user.hremployee
    except:
        messages.error(request, 'Employee record not found.')
        return redirect('hr:dashboard')

    document = get_object_or_404(
        EmployeeDocument,
        pk=pk,
        employee=employee,
        is_deleted=False
    )

    if request.method == 'POST':
        form = DocumentRenewalRequestForm(request.POST)
        if form.is_valid():
            renewal = form.save(document=document)
            messages.success(
                request,
                f'Renewal request for "{document.title}" submitted successfully! HR will process it.'
            )
            return redirect('hr:my_documents')
    else:
        form = DocumentRenewalRequestForm()

    return render(request, 'hr/documents/employee/request_renewal.html', {
        'form': form,
        'document': document,
    })


# ============================================================================
# HR VIEWS (Administrative Portal)
# ============================================================================

@login_required
@user_passes_test(is_staff)
def hr_documents_dashboard(request):
    """
    HR comprehensive document management dashboard
    Advanced search, filtering, and bulk operations
    """
    # Get all documents
    documents = EmployeeDocument.objects.filter(
        is_deleted=False
    ).select_related('employee').order_by('-created_at')

    # Apply search filters
    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        # Employee filter
        if form.cleaned_data.get('employee'):
            documents = documents.filter(employee=form.cleaned_data['employee'])

        # Document type filter
        if form.cleaned_data.get('document_type'):
            documents = documents.filter(document_type=form.cleaned_data['document_type'])

        # Status filter
        if form.cleaned_data.get('status'):
            documents = documents.filter(status=form.cleaned_data['status'])

        # Expiry date filters
        if form.cleaned_data.get('expiry_from'):
            documents = documents.filter(expiry_date__gte=form.cleaned_data['expiry_from'])

        if form.cleaned_data.get('expiry_to'):
            documents = documents.filter(expiry_date__lte=form.cleaned_data['expiry_to'])

        # Expiring within days
        if form.cleaned_data.get('expiring_within_days'):
            days = form.cleaned_data['expiring_within_days']
            today = timezone.now().date()
            target_date = today + timedelta(days=days)
            documents = documents.filter(
                expiry_date__isnull=False,
                expiry_date__lte=target_date,
                expiry_date__gte=today
            )

        # Verification status
        if form.cleaned_data.get('is_verified'):
            is_verified = form.cleaned_data['is_verified'] == 'true'
            documents = documents.filter(is_verified=is_verified)

        # Mandatory filter
        if form.cleaned_data.get('is_mandatory'):
            is_mandatory = form.cleaned_data['is_mandatory'] == 'true'
            documents = documents.filter(is_mandatory=is_mandatory)

        # Text search
        if form.cleaned_data.get('search_text'):
            search = form.cleaned_data['search_text']
            documents = documents.filter(
                Q(title__icontains=search) |
                Q(document_number__icontains=search) |
                Q(description__icontains=search) |
                Q(notes__icontains=search)
            )

        # Department filter
        if form.cleaned_data.get('department'):
            documents = documents.filter(
                employee__department=form.cleaned_data['department']
            )

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(documents, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_documents = documents.count()
    unverified = documents.filter(is_verified=False).count()

    today = timezone.now().date()
    expiring_30 = documents.filter(
        expiry_date__isnull=False,
        expiry_date__lte=today + timedelta(days=30),
        expiry_date__gte=today
    ).count()

    expired = documents.filter(
        expiry_date__isnull=False,
        expiry_date__lt=today
    ).count()

    mandatory_missing = EmployeeDocument.objects.filter(
        is_deleted=False,
        is_mandatory=True,
        status__in=[DocumentStatus.EXPIRED, DocumentStatus.EXPIRING_SOON]
    ).count()

    context = {
        'form': form,
        'page_obj': page_obj,
        'documents': page_obj,
        'total_documents': total_documents,
        'unverified_count': unverified,
        'expiring_30_count': expiring_30,
        'expired_count': expired,
        'mandatory_missing': mandatory_missing,
    }

    return render(request, 'hr/documents/hr/documents_dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def hr_upload_document(request):
    """
    HR staff upload document for any employee
    """
    if request.method == 'POST':
        form = HRDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, f'Document uploaded successfully for {document.employee}')
            return redirect('hr:hr_documents_dashboard')
    else:
        form = HRDocumentForm()

    context = {
        'form': form,
        'title': 'Upload Employee Document',
    }
    return render(request, 'hr/documents/hr/upload_document.html', context)


@login_required
@user_passes_test(is_staff)
def hr_expiry_dashboard(request):
    """
    HR dashboard focused on document expiry management
    """
    today = timezone.now().date()

    # Get expiring documents
    expiring_30 = EmployeeDocument.objects.filter(
        is_deleted=False,
        expiry_date__isnull=False,
        expiry_date__lte=today + timedelta(days=30),
        expiry_date__gte=today
    ).select_related('employee').order_by('expiry_date')

    expiring_60 = EmployeeDocument.objects.filter(
        is_deleted=False,
        expiry_date__isnull=False,
        expiry_date__lte=today + timedelta(days=60),
        expiry_date__gt=today + timedelta(days=30)
    ).select_related('employee').order_by('expiry_date')

    expiring_90 = EmployeeDocument.objects.filter(
        is_deleted=False,
        expiry_date__isnull=False,
        expiry_date__lte=today + timedelta(days=90),
        expiry_date__gt=today + timedelta(days=60)
    ).select_related('employee').order_by('expiry_date')

    # Get expired documents
    expired = EmployeeDocument.objects.filter(
        is_deleted=False,
        expiry_date__isnull=False,
        expiry_date__lt=today
    ).select_related('employee').order_by('expiry_date')

    # Get pending renewals
    pending_renewals = DocumentRenewal.objects.filter(
        status__in=['REQUESTED', 'IN_PROGRESS']
    ).select_related('document', 'document__employee').order_by('-request_date')

    # Group by document type
    expiring_by_type = expiring_30.values('document_type').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'expiring_30': expiring_30,
        'expiring_60': expiring_60,
        'expiring_90': expiring_90,
        'expired': expired,
        'pending_renewals': pending_renewals,
        'expiring_by_type': expiring_by_type,
        'today': today,
    }

    return render(request, 'hr/documents/hr/expiry_dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def hr_verify_document(request, pk):
    """
    HR verifies/approves employee document
    """
    document = get_object_or_404(
        EmployeeDocument,
        pk=pk,
        is_deleted=False
    )

    if request.method == 'POST':
        form = DocumentVerificationForm(request.POST)
        if form.is_valid():
            document.is_verified = form.cleaned_data['is_verified']
            document.verification_notes = form.cleaned_data['verification_notes']
            document.verified_by_id = request.user.id
            document.verified_at = timezone.now()
            document.save()

            if document.is_verified:
                messages.success(request, f'Document "{document.title}" verified successfully!')
            else:
                messages.warning(request, f'Document "{document.title}" marked as unverified.')

            return redirect('hr:hr_documents_dashboard')
    else:
        form = DocumentVerificationForm()

    return render(request, 'hr/documents/hr/verify_document.html', {
        'form': form,
        'document': document,
    })


@login_required
@user_passes_test(is_staff)
def hr_bulk_actions(request):
    """
    HR performs bulk actions on documents
    """
    if request.method == 'POST':
        form = BulkDocumentActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            document_ids = request.POST.getlist('document_ids')

            if not document_ids:
                messages.error(request, 'No documents selected.')
                return redirect('hr:hr_documents_dashboard')

            documents = EmployeeDocument.objects.filter(
                id__in=document_ids,
                is_deleted=False
            )

            if action == 'verify':
                documents.update(
                    is_verified=True,
                    verified_by_id=request.user.id,
                    verified_at=timezone.now()
                )
                messages.success(request, f'{documents.count()} document(s) marked as verified.')

            elif action == 'archive':
                documents.update(status=DocumentStatus.ARCHIVED)
                messages.success(request, f'{documents.count()} document(s) archived.')

            elif action == 'delete':
                documents.update(is_deleted=True)
                messages.success(request, f'{documents.count()} document(s) deleted.')

            elif action == 'export':
                # Export to Excel
                return export_documents_excel(documents)

            elif action == 'send_reminder':
                # Send expiry reminders
                count = send_expiry_reminders(documents)
                messages.success(request, f'Expiry reminders sent for {count} document(s).')

            return redirect('hr:hr_documents_dashboard')

    return redirect('hr:hr_documents_dashboard')


@login_required
@user_passes_test(is_staff)
def hr_document_detail(request, pk):
    """
    HR views full document details with all administrative info
    """
    document = get_object_or_404(
        EmployeeDocument,
        pk=pk,
        is_deleted=False
    )

    renewals = document.renewals.all().order_by('-request_date')
    alerts = document.expiry_alerts.all().order_by('-alert_date')[:10]

    context = {
        'document': document,
        'renewals': renewals,
        'alerts': alerts,
    }

    return render(request, 'hr/documents/hr/document_detail.html', context)


@login_required
@user_passes_test(is_staff)
def download_document(request, pk):
    """
    Download document file
    """
    document = get_object_or_404(EmployeeDocument, pk=pk, is_deleted=False)

    # Check permissions
    if not request.user.is_staff:
        # Check if user is the document owner
        try:
            if document.employee.user != request.user:
                messages.error(request, 'You do not have permission to download this document.')
                return redirect('hr:my_documents')
        except:
            messages.error(request, 'Permission denied.')
            return redirect('hr:my_documents')

    # Serve file (this would integrate with your file storage)
    # For now, returning a placeholder response
    messages.info(request, f'Download initiated for: {document.file_name}')
    return redirect(request.META.get('HTTP_REFERER', 'hr:my_documents'))


@login_required
@user_passes_test(is_staff)
def print_document_list(request):
    """
    Generate printable document list
    """
    # Get filtered documents based on query params
    documents = EmployeeDocument.objects.filter(is_deleted=False).select_related('employee')

    # Apply same filters as dashboard
    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        # Apply filters (same logic as hr_documents_dashboard)
        pass

    context = {
        'documents': documents,
        'print_date': timezone.now(),
    }

    return render(request, 'hr/documents/hr/print_list.html', context)


# Helper functions

def export_documents_excel(documents):
    """Export documents to Excel"""
    import xlsxwriter
    from io.BytesIO import BytesIO

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Documents')

    # Write headers
    headers = [
        'Employee No', 'Employee Name', 'Document Type', 'Title',
        'Document Number', 'Issue Date', 'Expiry Date', 'Status',
        'Verified', 'Mandatory'
    ]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    # Write data
    for row, doc in enumerate(documents, start=1):
        worksheet.write(row, 0, doc.employee.employee_no)
        worksheet.write(row, 1, doc.employee.get_full_name())
        worksheet.write(row, 2, doc.get_document_type_display())
        worksheet.write(row, 3, doc.title)
        worksheet.write(row, 4, doc.document_number)
        worksheet.write(row, 5, str(doc.issue_date) if doc.issue_date else '')
        worksheet.write(row, 6, str(doc.expiry_date) if doc.expiry_date else '')
        worksheet.write(row, 7, doc.get_status_display())
        worksheet.write(row, 8, 'Yes' if doc.is_verified else 'No')
        worksheet.write(row, 9, 'Yes' if doc.is_mandatory else 'No')

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=documents_{timezone.now().strftime("%Y%m%d")}.xlsx'

    return response


def send_expiry_reminders(documents):
    """Send expiry reminder notifications"""
    count = 0
    for doc in documents:
        if doc.expiry_date and doc.days_until_expiry and doc.days_until_expiry <= 30:
            # Create expiry alert
            ExpiryAlert.objects.create(
                document=doc,
                days_before_expiry=doc.days_until_expiry
            )
            count += 1
            # Send actual notification here (email/SMS)

    return count
