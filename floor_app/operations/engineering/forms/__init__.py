"""
Engineering Forms

Forms for design and BOM management.

MOVED FROM: floor_app.operations.inventory.forms
REASON: Engineering owns design and BOM definitions
"""

from django import forms
from floor_app.operations.engineering.models import (
    BitDesign, BitDesignRevision, BitDesignLevel, BitDesignType,
    BOMHeader, BOMLine,
)


class BitDesignForm(forms.ModelForm):
    """Form for creating/editing Bit Designs."""

    class Meta:
        model = BitDesign
        fields = [
            'design_code', 'name', 'level', 'bit_category', 'size_inches', 'connection_type',
            'blade_count', 'total_cutter_count', 'nozzle_count', 'tfa_range',
            'description'
        ]
        widgets = {
            'design_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., HP-X123'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'bit_category': forms.Select(attrs={'class': 'form-select'}),
            'size_inches': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g., 8.50'}),
            'connection_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 4-1/2 API REG'}),
            'blade_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_cutter_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'nozzle_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'tfa_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0.50-0.75'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['level'].queryset = BitDesignLevel.objects.filter(is_active=True)


class BitDesignRevisionForm(forms.ModelForm):
    """Form for creating/editing MAT Numbers (Bit Design Revisions)."""

    class Meta:
        model = BitDesignRevision
        fields = [
            'mat_number', 'bit_design', 'revision_code', 'design_type',
            'is_temporary', 'is_active', 'effective_date', 'obsolete_date',
            'superseded_by', 'change_reason', 'notes', 'erp_item_number',
            'erp_bom_number', 'standard_cost', 'last_purchase_cost'
        ]
        widgets = {
            'mat_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., HP-X123-M2'}),
            'bit_design': forms.Select(attrs={'class': 'form-select'}),
            'revision_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., M0, M1, M2'}),
            'design_type': forms.Select(attrs={'class': 'form-select'}),
            'is_temporary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'obsolete_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'superseded_by': forms.Select(attrs={'class': 'form-select'}),
            'change_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'erp_item_number': forms.TextInput(attrs={'class': 'form-control'}),
            'erp_bom_number': forms.TextInput(attrs={'class': 'form-control'}),
            'standard_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'last_purchase_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bit_design'].queryset = BitDesign.objects.filter(is_deleted=False)
        self.fields['design_type'].queryset = BitDesignType.objects.filter(is_active=True)
        self.fields['design_type'].required = False
        self.fields['superseded_by'].queryset = BitDesignRevision.objects.filter(is_deleted=False)
        self.fields['superseded_by'].required = False
        self.fields['obsolete_date'].required = False


class BOMHeaderForm(forms.ModelForm):
    """Form for creating/editing BOM Headers."""

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_mat'].queryset = BitDesignRevision.objects.filter(is_deleted=False)
        self.fields['source_mat'].queryset = BitDesignRevision.objects.filter(is_deleted=False)
        self.fields['source_mat'].required = False


__all__ = [
    'BitDesignForm',
    'BitDesignRevisionForm',
    'BOMHeaderForm',
]
