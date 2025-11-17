"""
Procurement Forms (PR, RFQ, PO, GRN, Invoice)
"""

from django import forms
from floor_app.operations.purchasing.models import (
    PurchaseRequisition,
    PurchaseRequisitionLine,
    RequestForQuotation,
    RFQLine,
    PurchaseOrder,
    PurchaseOrderLine,
    GoodsReceiptNote,
    GRNLine,
    SupplierInvoice,
    SupplierInvoiceLine,
    PurchaseReturn,
    PurchaseReturnLine,
)


class PurchaseRequisitionForm(forms.ModelForm):
    """Form for Purchase Requisition"""

    class Meta:
        model = PurchaseRequisition
        fields = [
            'pr_type', 'priority', 'requester_id', 'department_id',
            'cost_center', 'project_code', 'required_by_date',
            'delivery_location_id', 'delivery_address',
            'job_card_id', 'justification', 'notes'
        ]
        widgets = {
            'pr_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'requester_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'department_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost_center': forms.TextInput(attrs={'class': 'form-control'}),
            'project_code': forms.TextInput(attrs={'class': 'form-control'}),
            'required_by_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'delivery_location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'job_card_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'justification': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PRLineForm(forms.ModelForm):
    """Form for PR Line"""

    class Meta:
        model = PurchaseRequisitionLine
        fields = [
            'line_number', 'item_id', 'item_code', 'description',
            'quantity_requested', 'uom', 'estimated_unit_price',
            'suggested_supplier_id', 'notes'
        ]
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'uom': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'suggested_supplier_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PurchaseOrderForm(forms.ModelForm):
    """Form for Purchase Order"""

    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'po_type', 'buyer_id', 'department_id',
            'expected_delivery_date', 'delivery_location_id', 'delivery_address',
            'shipping_method', 'currency', 'payment_terms', 'incoterm',
            'discount_percentage', 'tax_percentage', 'shipping_cost', 'other_charges',
            'special_instructions', 'terms_and_conditions', 'notes'
        ]
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'po_type': forms.Select(attrs={'class': 'form-select'}),
            'buyer_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'department_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'delivery_location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'shipping_method': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'incoterm': forms.Select(attrs={'class': 'form-select'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'terms_and_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class POLineForm(forms.ModelForm):
    """Form for PO Line"""

    class Meta:
        model = PurchaseOrderLine
        fields = [
            'line_number', 'item_id', 'item_code', 'description',
            'quantity_ordered', 'uom', 'unit_price', 'promised_date', 'notes'
        ]
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_ordered': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'uom': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'promised_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class GoodsReceiptNoteForm(forms.ModelForm):
    """Form for Goods Receipt Note"""

    class Meta:
        model = GoodsReceiptNote
        fields = [
            'purchase_order', 'receipt_date', 'receipt_time', 'received_by_id',
            'delivery_note_number', 'waybill_number', 'carrier_name',
            'vehicle_number', 'driver_name', 'driver_id',
            'receiving_location_id', 'qa_hold_location_id',
            'total_packages', 'total_weight_kg', 'package_condition',
            'damage_notes', 'requires_inspection',
            'customs_declaration_number', 'customs_clearance_date',
            'import_permit_number', 'certificate_of_origin',
            'certificate_of_conformity', 'notes'
        ]
        widgets = {
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'receipt_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'receipt_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'received_by_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery_note_number': forms.TextInput(attrs={'class': 'form-control'}),
            'waybill_number': forms.TextInput(attrs={'class': 'form-control'}),
            'carrier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_id': forms.TextInput(attrs={'class': 'form-control'}),
            'receiving_location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'qa_hold_location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_packages': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'package_condition': forms.Select(attrs={'class': 'form-select'}),
            'damage_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'requires_inspection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'customs_declaration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customs_clearance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'import_permit_number': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_of_origin': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_of_conformity': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class GRNLineForm(forms.ModelForm):
    """Form for GRN Line"""

    class Meta:
        model = GRNLine
        fields = [
            'line_number', 'po_line', 'item_id', 'item_code', 'description',
            'quantity_ordered', 'quantity_received', 'uom', 'unit_price',
            'storage_location_id', 'storage_bin',
            'batch_number', 'expiry_date', 'manufacturer_batch',
            'requires_inspection', 'notes'
        ]
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'po_line': forms.Select(attrs={'class': 'form-select'}),
            'item_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_ordered': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'quantity_received': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'uom': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'storage_location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'storage_bin': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'manufacturer_batch': forms.TextInput(attrs={'class': 'form-control'}),
            'requires_inspection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SupplierInvoiceForm(forms.ModelForm):
    """Form for Supplier Invoice"""

    class Meta:
        model = SupplierInvoice
        fields = [
            'supplier', 'invoice_number', 'invoice_type',
            'invoice_date', 'due_date', 'posting_date',
            'purchase_order', 'grn',
            'currency', 'payment_terms', 'exchange_rate',
            'discount_amount', 'tax_amount', 'withholding_tax',
            'shipping_charges', 'other_charges',
            'gl_account', 'cost_center', 'notes'
        ]
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'posting_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'grn': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'exchange_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'withholding_tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'shipping_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gl_account': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_center': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PurchaseReturnForm(forms.ModelForm):
    """Form for Purchase Return"""

    class Meta:
        model = PurchaseReturn
        fields = [
            'supplier', 'purchase_order', 'grn',
            'reason', 'reason_detail', 'requested_action',
            'requester_id', 'deduct_from_inventory', 'notes'
        ]
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'grn': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'reason_detail': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'requested_action': forms.Select(attrs={'class': 'form-select'}),
            'requester_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'deduct_from_inventory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
