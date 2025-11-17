from django import forms
from .models import (
    Item, SerialUnit, BOMHeader, BOMLine, InventoryTransaction,
    ItemCategory, ConditionType, OwnershipType, Location, UnitOfMeasure,
    BitDesignRevision
)


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'sku', 'name', 'short_name', 'category', 'uom',
            'bit_design_revision', 'min_stock_qty', 'reorder_point',
            'reorder_qty', 'safety_stock', 'lead_time_days',
            'standard_cost', 'currency', 'is_active', 'is_purchasable',
            'is_producible', 'is_sellable', 'is_stockable',
            'primary_supplier', 'manufacturer_name', 'manufacturer_part_number',
            'weight_kg', 'volume_cbm', 'description', 'barcode'
        ]
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'uom': forms.Select(attrs={'class': 'form-select'}),
            'bit_design_revision': forms.Select(attrs={'class': 'form-select'}),
            'min_stock_qty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_point': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_qty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'safety_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'standard_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer_part_number': forms.TextInput(attrs={'class': 'form-control'}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'volume_cbm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SerialUnitForm(forms.ModelForm):
    class Meta:
        model = SerialUnit
        fields = [
            'item', 'serial_number', 'current_mat', 'location',
            'condition', 'ownership', 'status', 'manufacture_date',
            'received_date', 'warranty_expiry', 'acquisition_cost',
            'current_customer', 'notes'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'current_mat': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'ownership': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'manufacture_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'received_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'acquisition_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_customer': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BOMHeaderForm(forms.ModelForm):
    class Meta:
        model = BOMHeader
        fields = [
            'bom_number', 'name', 'description', 'bom_type', 'target_mat',
            'source_mat', 'revision', 'status', 'effective_date',
            'estimated_labor_hours', 'estimated_material_cost', 'notes'
        ]
        widgets = {
            'bom_number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'bom_type': forms.Select(attrs={'class': 'form-select'}),
            'target_mat': forms.Select(attrs={'class': 'form-select'}),
            'source_mat': forms.Select(attrs={'class': 'form-select'}),
            'revision': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_labor_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_material_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = [
            'transaction_type', 'item', 'serial_unit', 'quantity', 'uom',
            'from_location', 'to_location', 'from_condition', 'to_condition',
            'from_ownership', 'to_ownership', 'reference_type', 'reference_id',
            'unit_cost', 'reason_code', 'notes'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'serial_unit': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'uom': forms.Select(attrs={'class': 'form-select'}),
            'from_location': forms.Select(attrs={'class': 'form-select'}),
            'to_location': forms.Select(attrs={'class': 'form-select'}),
            'from_condition': forms.Select(attrs={'class': 'form-select'}),
            'to_condition': forms.Select(attrs={'class': 'form-select'}),
            'from_ownership': forms.Select(attrs={'class': 'form-select'}),
            'to_ownership': forms.Select(attrs={'class': 'form-select'}),
            'reference_type': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_id': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'reason_code': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class StockAdjustmentForm(forms.Form):
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(is_active=True, category__is_serialized=False),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Item'
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Location'
    )
    condition = forms.ModelChoiceField(
        queryset=ConditionType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Condition'
    )
    ownership = forms.ModelChoiceField(
        queryset=OwnershipType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Ownership'
    )
    quantity = forms.DecimalField(
        max_digits=12,
        decimal_places=4,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        help_text='Positive for increase, negative for decrease'
    )
    reason = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='ADJUSTMENT'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
