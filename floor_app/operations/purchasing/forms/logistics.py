"""
Logistics Forms (Transfers, Shipments, Customer Returns)
"""

from django import forms
from floor_app.operations.purchasing.models import (
    InternalTransferOrder,
    TransferOrderLine,
    OutboundShipment,
    ShipmentLine,
    CustomerReturn,
    CustomerReturnLine,
)


class InternalTransferOrderForm(forms.ModelForm):
    """Form for Internal Transfer Order"""

    class Meta:
        model = InternalTransferOrder
        fields = [
            'transfer_type', 'priority',
            'source_warehouse_id', 'source_location_id', 'source_location_name',
            'destination_warehouse_id', 'destination_location_id', 'destination_location_name',
            'requester_id', 'department_id',
            'required_by_date', 'approval_required',
            'job_card_id', 'bom_id', 'reason', 'notes'
        ]
        widgets = {
            'transfer_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'source_warehouse_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'source_location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'source_location_name': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_warehouse_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'destination_location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'destination_location_name': forms.TextInput(attrs={'class': 'form-control'}),
            'requester_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'department_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'required_by_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'approval_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'job_card_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'bom_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class TransferOrderLineForm(forms.ModelForm):
    """Form for Transfer Order Line"""

    class Meta:
        model = TransferOrderLine
        fields = [
            'line_number', 'item_id', 'item_code', 'description',
            'quantity_to_transfer', 'uom', 'unit_cost',
            'source_bin', 'destination_bin', 'batch_number', 'notes'
        ]
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_to_transfer': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'uom': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'source_bin': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_bin': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class OutboundShipmentForm(forms.ModelForm):
    """Form for Outbound Shipment"""

    class Meta:
        model = OutboundShipment
        fields = [
            'shipment_type', 'customer_id', 'customer_name', 'customer_reference',
            'delivery_contact_name', 'delivery_contact_phone',
            'delivery_address_line1', 'delivery_address_line2',
            'delivery_city', 'delivery_state', 'delivery_postal_code', 'delivery_country',
            'rig_name', 'rig_location', 'well_name', 'field_name',
            'source_warehouse_id', 'scheduled_ship_date', 'expected_delivery_date',
            'carrier_name', 'shipping_method', 'incoterm', 'currency',
            'shipping_cost', 'insurance_cost',
            'special_instructions', 'notes'
        ]
        widgets = {
            'shipment_type': forms.Select(attrs={'class': 'form-select'}),
            'customer_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_city': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_state': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_country': forms.TextInput(attrs={'class': 'form-control'}),
            'rig_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rig_location': forms.TextInput(attrs={'class': 'form-control'}),
            'well_name': forms.TextInput(attrs={'class': 'form-control'}),
            'field_name': forms.TextInput(attrs={'class': 'form-control'}),
            'source_warehouse_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'scheduled_ship_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'carrier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_method': forms.TextInput(attrs={'class': 'form-control'}),
            'incoterm': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'insurance_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ShipmentLineForm(forms.ModelForm):
    """Form for Shipment Line"""

    class Meta:
        model = ShipmentLine
        fields = [
            'line_number', 'item_id', 'item_code', 'description',
            'quantity_ordered', 'quantity_picked', 'quantity_shipped', 'uom',
            'unit_price', 'package_number', 'weight_kg', 'dimensions',
            'batch_number', 'notes'
        ]
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_ordered': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'quantity_picked': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'quantity_shipped': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'uom': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'package_number': forms.TextInput(attrs={'class': 'form-control'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class CustomerReturnForm(forms.ModelForm):
    """Form for Customer Return"""

    class Meta:
        model = CustomerReturn
        fields = [
            'customer_id', 'customer_name', 'customer_contact', 'customer_phone',
            'original_shipment', 'sales_order_id',
            'reason', 'reason_detail',
            'receiving_warehouse_id', 'qa_hold_location_id',
            'inspection_required', 'restock_to_inventory', 'notes'
        ]
        widgets = {
            'customer_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'original_shipment': forms.Select(attrs={'class': 'form-select'}),
            'sales_order_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'reason_detail': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'receiving_warehouse_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'qa_hold_location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'inspection_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'restock_to_inventory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class CustomerReturnLineForm(forms.ModelForm):
    """Form for Customer Return Line"""

    class Meta:
        model = CustomerReturnLine
        fields = [
            'line_number', 'item_id', 'item_code', 'description',
            'shipment_line', 'quantity_returned', 'uom',
            'condition', 'condition_notes', 'unit_price',
            'batch_number', 'notes'
        ]
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'shipment_line': forms.Select(attrs={'class': 'form-select'}),
            'quantity_returned': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'uom': forms.TextInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'condition_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
