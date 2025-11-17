from django import forms
from ..models import Equipment, MaintenanceRequest, Container


class QCodeGenerateForm(forms.Form):
    """Form for generating QR codes."""
    qcode_type = forms.ChoiceField(
        choices=[
            ('', '-- Select Type --'),
            ('EMPLOYEE', 'Employee'),
            ('JOB_CARD', 'Job Card'),
            ('BIT_SERIAL', 'Serial Unit'),
            ('EQUIPMENT', 'Equipment'),
            ('ITEM', 'Item'),
            ('LOCATION', 'Location'),
            ('BIT_BOX', 'Container/Box'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    object_id = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="ID of the target object"
    )

    label = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Optional label for the QR code"
    )


class EquipmentForm(forms.ModelForm):
    """Form for creating/editing equipment."""

    class Meta:
        model = Equipment
        fields = [
            'code', 'name', 'description', 'equipment_type',
            'manufacturer', 'model_number', 'serial_number',
            'location_id', 'location_name', 'department_id', 'department_name',
            'status', 'purchase_date', 'installation_date', 'warranty_expiry_date',
            'maintenance_interval_days', 'purchase_cost', 'current_value', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'equipment_type': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'location_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'department_name': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'installation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'warranty_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'maintenance_interval_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'purchase_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MaintenanceRequestForm(forms.ModelForm):
    """Form for creating maintenance requests."""

    class Meta:
        model = MaintenanceRequest
        fields = ['title', 'description', 'priority', 'maintenance_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-select'}),
        }


class MaintenanceCompleteForm(forms.ModelForm):
    """Form for completing maintenance requests."""

    class Meta:
        model = MaintenanceRequest
        fields = ['resolution_notes', 'parts_used', 'labor_hours', 'total_cost']
        widgets = {
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'parts_used': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'labor_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25'}),
            'total_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ContainerForm(forms.ModelForm):
    """Form for creating/editing containers."""

    class Meta:
        model = Container
        fields = [
            'code', 'name', 'container_type', 'status',
            'location_id', 'location_code', 'location_name',
            'max_capacity', 'dedicated_to_customer', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'container_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'location_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'location_code': forms.TextInput(attrs={'class': 'form-control'}),
            'location_name': forms.TextInput(attrs={'class': 'form-control'}),
            'max_capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'dedicated_to_customer': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BOMPickupForm(forms.Form):
    """Form for BOM material pickup."""
    quantity = forms.DecimalField(
        min_value=0.0001,
        decimal_places=4,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        help_text="Quantity to pickup"
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Optional notes"
    )


class ProcessActionForm(forms.Form):
    """Form for process step actions."""
    action = forms.ChoiceField(
        choices=[
            ('start', 'Start'),
            ('end', 'End'),
            ('pause', 'Pause'),
            ('resume', 'Resume'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Optional notes"
    )

    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text="Reason (required for pause)"
    )
