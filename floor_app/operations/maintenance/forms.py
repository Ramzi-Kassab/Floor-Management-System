"""
Forms for Maintenance & Asset Management module.
"""
from django import forms
from .models import (
    Asset, AssetDocument, AssetCategory, AssetLocation,
    MaintenanceRequest, WorkOrder,
    DowntimeEvent, PMTask,
)


class AssetForm(forms.ModelForm):
    """Form for creating/updating assets."""

    class Meta:
        model = Asset
        fields = [
            'asset_code', 'name', 'description',
            'category', 'location', 'parent_asset',
            'manufacturer', 'model_number', 'serial_number',
            'status', 'criticality', 'is_critical_production_asset',
            'installation_date', 'warranty_expiry_date',
            'purchase_date', 'purchase_cost', 'replacement_cost',
            'erp_asset_number', 'specifications', 'notes',
        ]
        widgets = {
            'asset_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'parent_asset': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'criticality': forms.Select(attrs={'class': 'form-select'}),
            'is_critical_production_asset': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'installation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warranty_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'replacement_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'erp_asset_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active categories and locations
        self.fields['category'].queryset = AssetCategory.objects.filter(is_deleted=False)
        self.fields['location'].queryset = AssetLocation.objects.filter(is_deleted=False, is_active=True)
        self.fields['parent_asset'].queryset = Asset.objects.filter(is_deleted=False)
        self.fields['parent_asset'].required = False


class AssetDocumentForm(forms.ModelForm):
    """Form for uploading asset documents."""

    class Meta:
        model = AssetDocument
        fields = ['title', 'doc_type', 'file', 'description', 'version']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'doc_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
        }


class MaintenanceRequestForm(forms.ModelForm):
    """Form for creating maintenance requests."""

    class Meta:
        model = MaintenanceRequest
        fields = [
            'asset', 'title', 'description', 'symptoms', 'priority',
            'requester_phone', 'requester_location',
            'is_production_stopped', 'estimated_downtime_minutes',
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief title of the issue'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the problem in detail...'
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observable symptoms (noise, smell, vibration, etc.)'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'requester_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'requester_location': forms.TextInput(attrs={'class': 'form-control'}),
            'is_production_stopped': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estimated_downtime_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.objects.filter(is_deleted=False, status='IN_SERVICE')
        self.fields['symptoms'].required = False
        self.fields['requester_phone'].required = False
        self.fields['requester_location'].required = False
        self.fields['estimated_downtime_minutes'].required = False


class WorkOrderForm(forms.ModelForm):
    """Form for creating/updating work orders."""

    class Meta:
        model = WorkOrder
        fields = [
            'asset', 'wo_type', 'priority', 'title', 'problem_description',
            'planned_start', 'planned_end', 'estimated_duration_minutes',
            'root_cause_category', 'root_cause_detail',
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'wo_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'problem_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'planned_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'planned_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'estimated_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'root_cause_category': forms.Select(attrs={'class': 'form-select'}),
            'root_cause_detail': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.objects.filter(is_deleted=False)
        self.fields['planned_start'].required = False
        self.fields['planned_end'].required = False
        self.fields['estimated_duration_minutes'].required = False
        self.fields['root_cause_category'].required = False
        self.fields['root_cause_detail'].required = False


class DowntimeEventForm(forms.ModelForm):
    """Form for recording downtime events."""

    class Meta:
        model = DowntimeEvent
        fields = [
            'asset', 'start_time', 'end_time', 'downtime_type',
            'reason_category', 'reason_detail', 'production_affected',
            'severity_score', 'notes',
        ]
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'downtime_type': forms.Select(attrs={'class': 'form-select'}),
            'reason_category': forms.Select(attrs={'class': 'form-select'}),
            'reason_detail': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'production_affected': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'severity_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.objects.filter(is_deleted=False)
        self.fields['end_time'].required = False
        self.fields['reason_detail'].required = False
        self.fields['notes'].required = False


class PMTaskCompleteForm(forms.Form):
    """Form for completing a PM task."""

    completion_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False,
        label='Completion Notes'
    )
    issues_found = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label='Issues Found'
    )
    follow_up_required = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        label='Follow-up Required'
    )
    follow_up_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label='Follow-up Notes'
    )
    meter_reading = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        required=False,
        label='Meter Reading at Completion'
    )
