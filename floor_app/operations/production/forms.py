from django import forms
from .models import (
    BatchOrder,
    JobCard,
    JobRouteStep,
    JobCutterEvaluationHeader,
    JobCutterEvaluationDetail,
    ApiThreadInspection,
    NdtReport,
    JobChecklistItem,
    OperationDefinition,
)


class BatchOrderForm(forms.ModelForm):
    """Form for creating/editing Batch Orders."""

    class Meta:
        model = BatchOrder
        fields = [
            'code', 'description', 'customer_name', 'main_order_number',
            'customer_reference', 'bit_family', 'target_quantity',
            'due_date', 'priority', 'current_location',
            'notes', 'special_instructions'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2025-ARDT-LV4-015'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'main_order_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'bit_family': forms.Select(attrs={'class': 'form-select'}),
            'target_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'current_location': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class JobCardForm(forms.ModelForm):
    """Form for creating/editing Job Cards."""

    class Meta:
        model = JobCard
        fields = [
            'job_card_number', 'batch_order', 'serial_unit',
            'initial_mat', 'current_mat', 'bom_header',
            'customer_name', 'customer_order_ref',
            'bit_size', 'bit_type',
            'well_name', 'rig_name', 'field_name',
            'job_type', 'priority',
            'planned_start_date', 'planned_end_date',
            'estimated_cost', 'quoted_price',
            'notes', 'special_instructions', 'customer_requirements',
            'rework_of', 'rework_reason'
        ]
        widgets = {
            'job_card_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., JC-2025-001'}),
            'batch_order': forms.Select(attrs={'class': 'form-select'}),
            'serial_unit': forms.Select(attrs={'class': 'form-select'}),
            'initial_mat': forms.Select(attrs={'class': 'form-select'}),
            'current_mat': forms.Select(attrs={'class': 'form-select'}),
            'bom_header': forms.Select(attrs={'class': 'form-select'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_order_ref': forms.TextInput(attrs={'class': 'form-control'}),
            'bit_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 12-1/4 inch'}),
            'bit_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., HDBS Type'}),
            'well_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rig_name': forms.TextInput(attrs={'class': 'form-control'}),
            'field_name': forms.TextInput(attrs={'class': 'form-control'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'planned_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quoted_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'customer_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rework_of': forms.Select(attrs={'class': 'form-select'}),
            'rework_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields optional
        self.fields['batch_order'].required = False
        self.fields['initial_mat'].required = False
        self.fields['current_mat'].required = False
        self.fields['bom_header'].required = False
        self.fields['rework_of'].required = False


class RouteStepForm(forms.ModelForm):
    """Form for adding/editing route steps."""

    class Meta:
        model = JobRouteStep
        fields = [
            'operation', 'sequence', 'planned_duration_hours',
            'operator', 'supervisor', 'result_notes'
        ]
        widgets = {
            'operation': forms.Select(attrs={'class': 'form-select'}),
            'sequence': forms.NumberInput(attrs={'class': 'form-control', 'step': 10}),
            'planned_duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25'}),
            'operator': forms.Select(attrs={'class': 'form-select'}),
            'supervisor': forms.Select(attrs={'class': 'form-select'}),
            'result_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['operator'].required = False
        self.fields['supervisor'].required = False


class RouteStepCompleteForm(forms.Form):
    """Form for completing a route step."""
    operator = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    result_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from floor_app.operations.hr.models import HREmployee
        self.fields['operator'].queryset = HREmployee.objects.filter(status='ACTIVE')


class CutterEvaluationHeaderForm(forms.ModelForm):
    """Form for creating cutter evaluation header."""

    class Meta:
        model = JobCutterEvaluationHeader
        fields = ['evaluation_type', 'layout', 'comments', 'source_description']
        widgets = {
            'evaluation_type': forms.Select(attrs={'class': 'form-select'}),
            'layout': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'source_description': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['layout'].required = False


class CutterEvaluationDetailForm(forms.ModelForm):
    """Form for individual cutter evaluation entry."""

    class Meta:
        model = JobCutterEvaluationDetail
        fields = ['row', 'column', 'symbol', 'condition_description', 'notes']
        widgets = {
            'row': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'column': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'symbol': forms.Select(attrs={'class': 'form-select'}),
            'condition_description': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ApiThreadInspectionForm(forms.ModelForm):
    """Form for API thread inspection."""

    class Meta:
        model = ApiThreadInspection
        fields = [
            'thread_type', 'thread_size', 'result', 'damage_type',
            'description_of_issue', 'measurement_results',
            'repair_action', 'final_notes'
        ]
        widgets = {
            'thread_type': forms.Select(attrs={'class': 'form-select'}),
            'thread_size': forms.TextInput(attrs={'class': 'form-control'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'damage_type': forms.Select(attrs={'class': 'form-select'}),
            'description_of_issue': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'measurement_results': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'repair_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'final_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class NdtReportForm(forms.ModelForm):
    """Form for NDT reports."""

    class Meta:
        model = NdtReport
        fields = [
            'test_type', 'test_procedure', 'test_area',
            'result', 'defect_severity',
            'defects_found', 'defect_locations', 'recommendations',
            'equipment_used', 'calibration_ref',
            'ambient_temp', 'humidity', 'notes', 'report_number'
        ]
        widgets = {
            'test_type': forms.Select(attrs={'class': 'form-select'}),
            'test_procedure': forms.TextInput(attrs={'class': 'form-control'}),
            'test_area': forms.TextInput(attrs={'class': 'form-control'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'defect_severity': forms.Select(attrs={'class': 'form-select'}),
            'defects_found': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'defect_locations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'equipment_used': forms.TextInput(attrs={'class': 'form-control'}),
            'calibration_ref': forms.TextInput(attrs={'class': 'form-control'}),
            'ambient_temp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'humidity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'report_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ChecklistItemCompleteForm(forms.Form):
    """Form for completing a checklist item."""
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    value_entered = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
