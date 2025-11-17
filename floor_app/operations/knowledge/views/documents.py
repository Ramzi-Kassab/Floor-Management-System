"""
Document management views.
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render

from ..models import Document
from ..forms import DocumentForm


class DocumentListView(LoginRequiredMixin, ListView):
    """List all documents."""
    model = Document
    template_name = 'knowledge/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        qs = Document.objects.filter(is_deleted=False)

        # Filter by type
        file_type = self.request.GET.get('type', '')
        if file_type:
            qs = qs.filter(file_type=file_type)

        # Search
        query = self.request.GET.get('q', '')
        if query:
            from django.db.models import Q
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['file_types'] = Document.FileType.choices
        return context


class DocumentUploadView(PermissionRequiredMixin, CreateView):
    """Upload new document."""
    model = Document
    form_class = DocumentForm
    template_name = 'knowledge/document_upload.html'
    permission_required = 'knowledge.add_document'
    success_url = reverse_lazy('knowledge:document_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Document uploaded successfully.')
        return super().form_valid(form)


@login_required
def document_detail(request, public_id):
    """View document details."""
    document = get_object_or_404(Document, public_id=public_id, is_deleted=False)

    context = {
        'document': document,
        'articles_using': document.articles.filter(is_deleted=False),
        'instructions_using': document.instructions.filter(is_deleted=False),
    }

    return render(request, 'knowledge/document_detail.html', context)


@login_required
def document_download(request, public_id):
    """Download a document file."""
    document = get_object_or_404(Document, public_id=public_id, is_deleted=False)

    if not document.file:
        return HttpResponse('File not found', status=404)

    document.increment_download()

    response = FileResponse(
        document.file.open('rb'),
        as_attachment=True,
        filename=document.filename
    )

    return response
