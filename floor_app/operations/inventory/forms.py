from django import forms
from .models import (
    Item, SerialUnit, InventoryTransaction,
    ItemCategory, ConditionType, OwnershipType, Location, UnitOfMeasure,
)
# Models moved to engineering app:
from floor_app.operations.engineering.models import (
    BitDesign, BitDesignRevision, BitDesignLevel, BitDesignType,
    BOMHeader, BOMLine,
)


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'sku', 'name', 'short_name', 'category', 'uom',
            'bit_design_revision', 'reorder_point',  # Removed min_stock_qty - redundant
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
            # Removed min_stock_qty widget - field is redundant with reorder_point
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
            'received_date', 'last_run_date', 'warranty_expiry', 'acquisition_cost',
            'current_book_value', 'current_customer', 'current_job_reference', 'notes'
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
            'last_run_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'acquisition_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_book_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_customer': forms.TextInput(attrs={'class': 'form-control'}),
            'current_job_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ⚠️ DEPRECATED - BOM and Design forms have moved to engineering app
# Import from: floor_app.operations.engineering.forms
#
# These form imports are kept for backwards compatibility but will be removed in a future update.
# Please update your imports to use:
#   from floor_app.operations.engineering.forms import BOMHeaderForm, BitDesignForm, BitDesignRevisionForm

from floor_app.operations.engineering.forms import (
    BOMHeaderForm, BitDesignForm, BitDesignRevisionForm
)


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


class LocationForm(forms.ModelForm):
    """Form for creating/editing Inventory Locations."""

    class Meta:
        model = Location
        fields = [
            'code', 'name', 'location_type', 'parent_location',
            'address', 'gps_coordinates', 'max_capacity', 'capacity_uom',
            'is_active', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., WH-01, BIN-A1-01'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location_type': forms.Select(attrs={'class': 'form-select'}),
            'parent_location': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'gps_coordinates': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 24.7136,46.6753'}),
            'max_capacity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacity_uom': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_location'].queryset = Location.objects.filter(is_active=True, is_deleted=False)
        self.fields['parent_location'].required = False
        self.fields['capacity_uom'].queryset = UnitOfMeasure.objects.filter(is_active=True)
        self.fields['capacity_uom'].required = False
        self.fields['max_capacity'].required = False
        self.fields['address'].required = False
        self.fields['gps_coordinates'].required = False


# Forms moved to engineering app - see imports above
