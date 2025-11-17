"""
Purchasing & Logistics Views

Comprehensive views for procurement, logistics, and supplier management.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta

from .models import (
    Supplier, SupplierItem, SupplierContact,
    PurchaseRequisition, PurchaseRequisitionLine,
    RequestForQuotation, RFQLine, SupplierQuotation,
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceiptNote, GRNLine, QualityInspection,
    PurchaseReturn, PurchaseReturnLine,
    SupplierInvoice, SupplierInvoiceLine,
    InternalTransferOrder, TransferOrderLine,
    OutboundShipment, ShipmentLine,
    CustomerReturn, CustomerReturnLine,
)
from .forms.supplier import SupplierForm, SupplierContactForm, SupplierItemForm
from .forms.procurement import (
    PurchaseRequisitionForm, PRLineForm,
    PurchaseOrderForm, POLineForm,
    GoodsReceiptNoteForm, GRNLineForm,
    SupplierInvoiceForm, PurchaseReturnForm,
)
from .forms.logistics import (
    InternalTransferOrderForm, TransferOrderLineForm,
    OutboundShipmentForm, ShipmentLineForm,
    CustomerReturnForm, CustomerReturnLineForm,
)
from .services import DocumentNumberingService


# ==================== DASHBOARD ====================

@login_required
def dashboard(request):
    """Main purchasing dashboard with KPIs and statistics"""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    context = {
        # Supplier KPIs
        'total_suppliers': Supplier.objects.count(),
        'active_suppliers': Supplier.objects.filter(status='ACTIVE').count(),
        'pending_suppliers': Supplier.objects.filter(status='PENDING_APPROVAL').count(),

        # PR Statistics
        'prs_pending_approval': PurchaseRequisition.objects.filter(
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        ).count(),
        'prs_approved': PurchaseRequisition.objects.filter(
            status='APPROVED',
            final_approval_at__gte=thirty_days_ago
        ).count(),

        # PO Statistics
        'open_pos': PurchaseOrder.objects.filter(
            status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED']
        ).count(),
        'pos_pending_approval': PurchaseOrder.objects.filter(
            status='PENDING_APPROVAL'
        ).count(),
        'total_po_value': PurchaseOrder.objects.filter(
            status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED', 'FULLY_RECEIVED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0,

        # GRN Statistics
        'pending_inspections': GoodsReceiptNote.objects.filter(
            status__in=['PENDING_INSPECTION', 'UNDER_INSPECTION']
        ).count(),
        'grns_to_post': GoodsReceiptNote.objects.filter(
            status='INSPECTION_COMPLETE'
        ).count(),

        # Invoice Statistics
        'invoices_pending_payment': SupplierInvoice.objects.filter(
            payment_status__in=['NOT_PAID', 'PARTIAL']
        ).count(),
        'overdue_invoices': SupplierInvoice.objects.filter(
            payment_status='OVERDUE'
        ).count(),
        'total_payables': SupplierInvoice.objects.filter(
            payment_status__in=['NOT_PAID', 'PARTIAL', 'OVERDUE']
        ).aggregate(total=Sum('amount_outstanding'))['total'] or 0,

        # Logistics
        'shipments_in_progress': OutboundShipment.objects.filter(
            status__in=['PICKING', 'PACKED', 'READY_TO_SHIP', 'SHIPPED', 'IN_TRANSIT']
        ).count(),
        'pending_transfers': InternalTransferOrder.objects.filter(
            status__in=['PENDING_APPROVAL', 'APPROVED', 'IN_TRANSIT']
        ).count(),
        'customer_returns_pending': CustomerReturn.objects.filter(
            status__in=['REQUESTED', 'APPROVED', 'SHIPPED', 'RECEIVED', 'INSPECTING']
        ).count(),

        # Recent Documents
        'recent_pos': PurchaseOrder.objects.order_by('-created_at')[:5],
        'recent_grns': GoodsReceiptNote.objects.order_by('-created_at')[:5],
        'recent_shipments': OutboundShipment.objects.order_by('-created_at')[:5],
    }

    return render(request, 'purchasing/dashboard.html', context)


# ==================== SUPPLIER MANAGEMENT ====================

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'purchasing/supplier/list.html'
    context_object_name = 'suppliers'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        classification = self.request.GET.get('classification')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)
        if classification:
            queryset = queryset.filter(classification=classification)
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(primary_email__icontains=search)
            )
        return queryset


class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'purchasing/supplier/detail.html'
    context_object_name = 'supplier'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.object
        context['contacts'] = supplier.contacts.all()
        context['items'] = supplier.supplier_items.all()[:10]
        context['recent_pos'] = supplier.purchase_orders.order_by('-order_date')[:5]
        context['recent_invoices'] = supplier.invoices.order_by('-invoice_date')[:5]
        return context


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'purchasing/supplier/form.html'
    success_url = reverse_lazy('purchasing:supplier_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Supplier {form.instance.code} created successfully.')
        return super().form_valid(form)


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'purchasing/supplier/form.html'

    def get_success_url(self):
        return reverse('purchasing:supplier_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Supplier {form.instance.code} updated successfully.')
        return super().form_valid(form)


# ==================== PURCHASE REQUISITION ====================

class PRListView(LoginRequiredMixin, ListView):
    model = PurchaseRequisition
    template_name = 'purchasing/pr/list.html'
    context_object_name = 'requisitions'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')

        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset


class PRDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseRequisition
    template_name = 'purchasing/pr/detail.html'
    context_object_name = 'pr'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all()
        return context


class PRCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseRequisition
    form_class = PurchaseRequisitionForm
    template_name = 'purchasing/pr/form.html'

    def form_valid(self, form):
        form.instance.pr_number = DocumentNumberingService.get_next_pr_number()
        form.instance.created_by = self.request.user
        messages.success(self.request, f'PR {form.instance.pr_number} created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('purchasing:pr_detail', kwargs={'pk': self.object.pk})


@login_required
def pr_submit(request, pk):
    """Submit PR for approval"""
    pr = get_object_or_404(PurchaseRequisition, pk=pk)
    if pr.submit(request.user):
        messages.success(request, f'PR {pr.pr_number} submitted for approval.')
    else:
        messages.error(request, 'PR cannot be submitted in its current state.')
    return redirect('purchasing:pr_detail', pk=pk)


@login_required
def pr_approve(request, pk):
    """Approve PR"""
    pr = get_object_or_404(PurchaseRequisition, pk=pk)
    # Get approver employee ID from user (placeholder)
    approver_id = request.user.id
    notes = request.POST.get('notes', '')

    if pr.approve_final(approver_id, notes):
        messages.success(request, f'PR {pr.pr_number} approved.')
    else:
        messages.error(request, 'PR cannot be approved in its current state.')
    return redirect('purchasing:pr_detail', pk=pk)


# ==================== PURCHASE ORDER ====================

class POListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'purchasing/po/list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        supplier = self.request.GET.get('supplier')

        if status:
            queryset = queryset.filter(status=status)
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        return queryset


class PODetailView(LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchasing/po/detail.html'
    context_object_name = 'po'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all()
        context['grns'] = self.object.grns.all()
        context['invoices'] = self.object.invoices.all()
        return context


class POCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchasing/po/form.html'

    def form_valid(self, form):
        form.instance.po_number = DocumentNumberingService.get_next_po_number()
        form.instance.created_by = self.request.user
        messages.success(self.request, f'PO {form.instance.po_number} created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('purchasing:po_detail', kwargs={'pk': self.object.pk})


@login_required
def po_submit(request, pk):
    """Submit PO for approval"""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if po.submit_for_approval(request.user):
        messages.success(request, f'PO {po.po_number} submitted for approval.')
    else:
        messages.error(request, 'PO cannot be submitted in its current state.')
    return redirect('purchasing:po_detail', pk=pk)


@login_required
def po_approve(request, pk):
    """Approve PO"""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    approver_id = request.user.id
    notes = request.POST.get('notes', '')

    if po.approve(approver_id, notes):
        messages.success(request, f'PO {po.po_number} approved.')
    else:
        messages.error(request, 'PO cannot be approved in its current state.')
    return redirect('purchasing:po_detail', pk=pk)


@login_required
def po_send(request, pk):
    """Send PO to supplier"""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    method = request.POST.get('method', 'EMAIL')

    if po.send_to_supplier(request.user, method):
        messages.success(request, f'PO {po.po_number} sent to supplier.')
    else:
        messages.error(request, 'PO cannot be sent in its current state.')
    return redirect('purchasing:po_detail', pk=pk)


# ==================== GOODS RECEIPT NOTE ====================

class GRNListView(LoginRequiredMixin, ListView):
    model = GoodsReceiptNote
    template_name = 'purchasing/grn/list.html'
    context_object_name = 'grns'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')

        if status:
            queryset = queryset.filter(status=status)
        return queryset


class GRNDetailView(LoginRequiredMixin, DetailView):
    model = GoodsReceiptNote
    template_name = 'purchasing/grn/detail.html'
    context_object_name = 'grn'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all()
        return context


class GRNCreateView(LoginRequiredMixin, CreateView):
    model = GoodsReceiptNote
    form_class = GoodsReceiptNoteForm
    template_name = 'purchasing/grn/form.html'

    def form_valid(self, form):
        form.instance.grn_number = DocumentNumberingService.get_next_grn_number()
        form.instance.created_by = self.request.user
        messages.success(self.request, f'GRN {form.instance.grn_number} created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('purchasing:grn_detail', kwargs={'pk': self.object.pk})


@login_required
def grn_post(request, pk):
    """Post GRN to inventory"""
    grn = get_object_or_404(GoodsReceiptNote, pk=pk)
    if grn.post_to_inventory(request.user):
        messages.success(request, f'GRN {grn.grn_number} posted to inventory.')
    else:
        messages.error(request, 'GRN cannot be posted in its current state.')
    return redirect('purchasing:grn_detail', pk=pk)


# ==================== SUPPLIER INVOICE ====================

class InvoiceListView(LoginRequiredMixin, ListView):
    model = SupplierInvoice
    template_name = 'purchasing/invoice/list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        payment_status = self.request.GET.get('payment_status')

        if status:
            queryset = queryset.filter(status=status)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        return queryset


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = SupplierInvoice
    template_name = 'purchasing/invoice/detail.html'
    context_object_name = 'invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all()
        return context


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = SupplierInvoice
    form_class = SupplierInvoiceForm
    template_name = 'purchasing/invoice/form.html'

    def form_valid(self, form):
        form.instance.internal_reference = DocumentNumberingService.get_next_invoice_reference()
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Invoice {form.instance.internal_reference} created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('purchasing:invoice_detail', kwargs={'pk': self.object.pk})


@login_required
def invoice_three_way_match(request, pk):
    """Perform three-way matching on invoice"""
    invoice = get_object_or_404(SupplierInvoice, pk=pk)
    is_matched, notes = invoice.perform_three_way_match()

    if is_matched:
        messages.success(request, 'Invoice matched successfully (PO ↔ GRN ↔ Invoice).')
    else:
        messages.warning(request, f'Matching incomplete: {notes}')

    return redirect('purchasing:invoice_detail', pk=pk)


# ==================== TRANSFERS ====================

class TransferListView(LoginRequiredMixin, ListView):
    model = InternalTransferOrder
    template_name = 'purchasing/transfer/list.html'
    context_object_name = 'transfers'
    paginate_by = 20


class TransferDetailView(LoginRequiredMixin, DetailView):
    model = InternalTransferOrder
    template_name = 'purchasing/transfer/detail.html'
    context_object_name = 'transfer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all()
        return context


class TransferCreateView(LoginRequiredMixin, CreateView):
    model = InternalTransferOrder
    form_class = InternalTransferOrderForm
    template_name = 'purchasing/transfer/form.html'

    def form_valid(self, form):
        form.instance.transfer_number = DocumentNumberingService.get_next_transfer_number()
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Transfer Order {form.instance.transfer_number} created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('purchasing:transfer_detail', kwargs={'pk': self.object.pk})


# ==================== SHIPMENTS ====================

class ShipmentListView(LoginRequiredMixin, ListView):
    model = OutboundShipment
    template_name = 'purchasing/shipment/list.html'
    context_object_name = 'shipments'
    paginate_by = 20


class ShipmentDetailView(LoginRequiredMixin, DetailView):
    model = OutboundShipment
    template_name = 'purchasing/shipment/detail.html'
    context_object_name = 'shipment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all()
        return context


class ShipmentCreateView(LoginRequiredMixin, CreateView):
    model = OutboundShipment
    form_class = OutboundShipmentForm
    template_name = 'purchasing/shipment/form.html'

    def form_valid(self, form):
        form.instance.shipment_number = DocumentNumberingService.get_next_shipment_number()
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Shipment {form.instance.shipment_number} created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('purchasing:shipment_detail', kwargs={'pk': self.object.pk})


@login_required
def shipment_confirm_delivery(request, pk):
    """Confirm shipment delivery"""
    shipment = get_object_or_404(OutboundShipment, pk=pk)
    delivered_to = request.POST.get('delivered_to', '')
    notes = request.POST.get('notes', '')

    if shipment.confirm_delivery(delivered_to, notes):
        messages.success(request, f'Shipment {shipment.shipment_number} delivery confirmed.')
    else:
        messages.error(request, 'Cannot confirm delivery in current state.')
    return redirect('purchasing:shipment_detail', pk=pk)


# ==================== CUSTOMER RETURNS ====================

class CustomerReturnListView(LoginRequiredMixin, ListView):
    model = CustomerReturn
    template_name = 'purchasing/customer_return/list.html'
    context_object_name = 'returns'
    paginate_by = 20


class CustomerReturnDetailView(LoginRequiredMixin, DetailView):
    model = CustomerReturn
    template_name = 'purchasing/customer_return/detail.html'
    context_object_name = 'return_order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all()
        return context


class CustomerReturnCreateView(LoginRequiredMixin, CreateView):
    model = CustomerReturn
    form_class = CustomerReturnForm
    template_name = 'purchasing/customer_return/form.html'

    def form_valid(self, form):
        form.instance.return_number = DocumentNumberingService.get_next_customer_return_number()
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Customer Return {form.instance.return_number} created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('purchasing:customer_return_detail', kwargs={'pk': self.object.pk})


# ==================== API ENDPOINTS ====================

@login_required
def api_supplier_search(request):
    """API endpoint for supplier search"""
    query = request.GET.get('q', '')
    suppliers = Supplier.objects.filter(
        Q(code__icontains=query) | Q(name__icontains=query)
    )[:10]

    data = [
        {
            'id': s.id,
            'code': s.code,
            'name': s.name,
            'text': f"{s.code} - {s.name}"
        }
        for s in suppliers
    ]
    return JsonResponse({'results': data})


@login_required
def api_po_search(request):
    """API endpoint for PO search"""
    query = request.GET.get('q', '')
    supplier_id = request.GET.get('supplier')

    pos = PurchaseOrder.objects.filter(po_number__icontains=query)
    if supplier_id:
        pos = pos.filter(supplier_id=supplier_id)
    pos = pos[:10]

    data = [
        {
            'id': po.id,
            'po_number': po.po_number,
            'supplier': po.supplier.name,
            'text': f"{po.po_number} - {po.supplier.code}"
        }
        for po in pos
    ]
    return JsonResponse({'results': data})


@login_required
def api_dashboard_stats(request):
    """API endpoint for dashboard statistics (AJAX refresh)"""
    stats = {
        'open_pos': PurchaseOrder.objects.filter(
            status__in=['APPROVED', 'SENT', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED']
        ).count(),
        'pending_inspections': GoodsReceiptNote.objects.filter(
            status__in=['PENDING_INSPECTION', 'UNDER_INSPECTION']
        ).count(),
        'overdue_invoices': SupplierInvoice.objects.filter(
            payment_status='OVERDUE'
        ).count(),
    }
    return JsonResponse(stats)
