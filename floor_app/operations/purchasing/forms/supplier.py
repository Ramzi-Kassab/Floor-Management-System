"""
Supplier Management Forms
"""

from django import forms
from floor_app.operations.purchasing.models import (
    Supplier,
    SupplierItem,
    SupplierContact,
)


class SupplierForm(forms.ModelForm):
    """Form for creating and editing suppliers"""

    class Meta:
        model = Supplier
        fields = [
            'code', 'name', 'legal_name', 'classification', 'status',
            'primary_email', 'secondary_email', 'phone', 'fax', 'website',
            'address_line1', 'address_line2', 'city', 'state_province',
            'postal_code', 'country',
            'default_currency', 'payment_terms', 'default_incoterm',
            'credit_limit', 'discount_percentage',
            'tax_id', 'cr_number', 'gosi_number', 'saudization_percentage',
            'bank_name', 'bank_branch', 'bank_account_number',
            'bank_iban', 'bank_swift_code',
            'iso_certified', 'iso_certificate_number', 'iso_expiry_date',
            'api_certified', 'api_certificate_number', 'api_expiry_date',
            'notes', 'internal_notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'classification': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'primary_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'secondary_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state_province': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'default_currency': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.Select(attrs={'class': 'form-select'}),
            'default_incoterm': forms.Select(attrs={'class': 'form-select'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'cr_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gosi_number': forms.TextInput(attrs={'class': 'form-control'}),
            'saudization_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_branch': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_iban': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_swift_code': forms.TextInput(attrs={'class': 'form-control'}),
            'iso_certified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'iso_certificate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'iso_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'api_certified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'api_certificate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'api_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SupplierContactForm(forms.ModelForm):
    """Form for supplier contacts"""

    class Meta:
        model = SupplierContact
        fields = [
            'name', 'title', 'department', 'email', 'phone',
            'mobile', 'is_primary', 'is_active', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SupplierItemForm(forms.ModelForm):
    """Form for supplier item catalog"""

    class Meta:
        model = SupplierItem
        fields = [
            'item_id', 'supplier_part_number', 'supplier_description',
            'unit_price', 'currency', 'price_valid_from', 'price_valid_until',
            'minimum_order_quantity', 'order_multiple', 'pack_size',
            'lead_time_days', 'safety_lead_time_days',
            'is_preferred', 'is_active',
            'quality_grade', 'requires_inspection', 'inspection_plan',
            'notes'
        ]
        widgets = {
            'item_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'supplier_part_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'price_valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'price_valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'minimum_order_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'order_multiple': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'pack_size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'safety_lead_time_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_preferred': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'quality_grade': forms.TextInput(attrs={'class': 'form-control'}),
            'requires_inspection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inspection_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
