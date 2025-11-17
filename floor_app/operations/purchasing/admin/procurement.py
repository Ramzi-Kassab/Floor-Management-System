"""
Procurement Admin Configuration (PR, RFQ, PO, GRN, Invoice)
"""

from django.contrib import admin
from floor_app.operations.purchasing.models import (
    PurchaseRequisition,
    PurchaseRequisitionLine,
    RequestForQuotation,
    RFQLine,
    SupplierQuotation,
    SupplierQuotationLine,
    PurchaseOrder,
    PurchaseOrderLine,
    GoodsReceiptNote,
    GRNLine,
    QualityInspection,
    PurchaseReturn,
    PurchaseReturnLine,
    SupplierInvoice,
    SupplierInvoiceLine,
)


# ========== Purchase Requisition ==========
class PRLineInline(admin.TabularInline):
    model = PurchaseRequisitionLine
    extra = 1
    fields = [
        'line_number', 'item_id', 'item_code', 'description',
        'quantity_requested', 'uom', 'estimated_unit_price',
        'total_estimated_cost', 'quantity_ordered', 'is_fully_ordered'
    ]
    readonly_fields = ['total_estimated_cost', 'is_fully_ordered']


@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = [
        'pr_number', 'pr_type', 'status', 'priority',
        'requester_id', 'request_date', 'required_by_date',
        'total_estimated_value'
    ]
    list_filter = ['status', 'pr_type', 'priority', 'request_date']
    search_fields = ['pr_number', 'justification']
    readonly_fields = [
        'public_id', 'pr_number', 'total_estimated_value',
        'submitted_at', 'submitted_by',
        'first_approval_at', 'second_approval_at', 'final_approval_at',
        'rejected_at', 'created_at', 'updated_at'
    ]
    inlines = [PRLineInline]
    date_hierarchy = 'request_date'


# ========== RFQ ==========
class RFQLineInline(admin.TabularInline):
    model = RFQLine
    extra = 1
    fields = ['line_number', 'item_id', 'item_code', 'description', 'quantity', 'uom']


@admin.register(RequestForQuotation)
class RequestForQuotationAdmin(admin.ModelAdmin):
    list_display = [
        'rfq_number', 'title', 'status', 'issue_date',
        'response_deadline', 'suppliers_invited', 'quotations_received'
    ]
    list_filter = ['status', 'issue_date']
    search_fields = ['rfq_number', 'title']
    readonly_fields = ['public_id', 'rfq_number', 'suppliers_invited', 'quotations_received']
    inlines = [RFQLineInline]


class QuotationLineInline(admin.TabularInline):
    model = SupplierQuotationLine
    extra = 0
    fields = [
        'line_number', 'rfq_line', 'quantity_quoted', 'unit_price',
        'total_price', 'lead_time_days', 'meets_specifications'
    ]
    readonly_fields = ['total_price']


@admin.register(SupplierQuotation)
class SupplierQuotationAdmin(admin.ModelAdmin):
    list_display = [
        'rfq', 'supplier', 'quotation_number', 'status',
        'received_date', 'valid_until', 'total_amount', 'is_selected'
    ]
    list_filter = ['status', 'is_selected', 'received_date']
    search_fields = ['quotation_number', 'supplier__code', 'supplier__name']
    readonly_fields = ['public_id', 'subtotal', 'total_amount']
    inlines = [QuotationLineInline]


# ========== Purchase Order ==========
class POLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    fields = [
        'line_number', 'item_id', 'item_code', 'description',
        'quantity_ordered', 'uom', 'unit_price', 'total_price',
        'quantity_received', 'is_fully_received'
    ]
    readonly_fields = ['total_price', 'is_fully_received']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number', 'supplier', 'status', 'order_date',
        'expected_delivery_date', 'total_amount', 'currency'
    ]
    list_filter = ['status', 'order_date', 'supplier']
    search_fields = ['po_number', 'supplier__code', 'supplier__name']
    readonly_fields = [
        'public_id', 'po_number', 'subtotal', 'discount_amount',
        'tax_amount', 'total_amount',
        'submitted_at', 'approved_at', 'sent_at', 'acknowledged_at',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['supplier', 'purchase_requisition', 'supplier_quotation']
    inlines = [POLineInline]
    date_hierarchy = 'order_date'


# ========== GRN ==========
class GRNLineInline(admin.TabularInline):
    model = GRNLine
    extra = 0
    fields = [
        'line_number', 'item_id', 'item_code', 'description',
        'quantity_ordered', 'quantity_received', 'quantity_accepted',
        'quantity_rejected', 'inspection_result'
    ]


class QualityInspectionInline(admin.TabularInline):
    model = QualityInspection
    extra = 0
    fk_name = 'grn_line'
    fields = [
        'parameter', 'specification', 'actual_value',
        'result', 'is_critical', 'inspector_id'
    ]


@admin.register(GoodsReceiptNote)
class GoodsReceiptNoteAdmin(admin.ModelAdmin):
    list_display = [
        'grn_number', 'purchase_order', 'status', 'receipt_date',
        'inspection_status', 'total_packages', 'total_weight_kg'
    ]
    list_filter = ['status', 'inspection_status', 'receipt_date']
    search_fields = ['grn_number', 'purchase_order__po_number', 'delivery_note_number']
    readonly_fields = [
        'public_id', 'grn_number', 'inspection_completed_at',
        'posted_at', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['purchase_order']
    inlines = [GRNLineInline]
    date_hierarchy = 'receipt_date'


# ========== Purchase Returns ==========
class PurchaseReturnLineInline(admin.TabularInline):
    model = PurchaseReturnLine
    extra = 0
    fields = [
        'line_number', 'item_id', 'item_code', 'description',
        'quantity_to_return', 'uom', 'unit_price', 'total_value', 'reason'
    ]
    readonly_fields = ['total_value']


@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(admin.ModelAdmin):
    list_display = [
        'return_number', 'supplier', 'status', 'return_date',
        'reason', 'requested_action', 'total_return_value'
    ]
    list_filter = ['status', 'reason', 'requested_action', 'return_date']
    search_fields = ['return_number', 'supplier__code', 'rma_number']
    readonly_fields = [
        'public_id', 'return_number', 'total_return_value',
        'rma_requested_at', 'rma_approved_at',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['supplier', 'purchase_order', 'grn']
    inlines = [PurchaseReturnLineInline]


# ========== Supplier Invoice ==========
class SupplierInvoiceLineInline(admin.TabularInline):
    model = SupplierInvoiceLine
    extra = 0
    fields = [
        'line_number', 'item_id', 'item_code', 'description',
        'quantity_invoiced', 'uom', 'unit_price', 'total_amount',
        'tax_rate', 'tax_amount'
    ]
    readonly_fields = ['total_amount', 'tax_amount']


@admin.register(SupplierInvoice)
class SupplierInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'internal_reference', 'invoice_number', 'supplier',
        'status', 'payment_status', 'invoice_date', 'due_date',
        'total_amount', 'amount_paid', 'amount_outstanding'
    ]
    list_filter = ['status', 'payment_status', 'invoice_date', 'supplier']
    search_fields = [
        'internal_reference', 'invoice_number',
        'supplier__code', 'supplier__name'
    ]
    readonly_fields = [
        'public_id', 'internal_reference', 'subtotal', 'total_amount',
        'amount_in_base_currency', 'amount_outstanding',
        'quantity_variance', 'price_variance',
        'verified_at', 'approved_at',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['supplier', 'purchase_order', 'grn']
    inlines = [SupplierInvoiceLineInline]
    date_hierarchy = 'invoice_date'
