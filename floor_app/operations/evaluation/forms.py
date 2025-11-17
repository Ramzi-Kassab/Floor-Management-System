from django import forms
from .models import (
    EvaluationSession,
    EvaluationCell,
    ThreadInspection,
    NDTInspection,
    TechnicalInstructionInstance,
    RequirementInstance,
    BitType,
    BitSection,
    FeatureCode,
    CutterEvaluationCode,
    TechnicalInstructionTemplate,
    RequirementTemplate,
)


class EvaluationSessionForm(forms.ModelForm):
    """Form for creating/editing Evaluation Sessions."""

    class Meta:
        model = EvaluationSession
        fields = [
            'session_number', 'job_card', 'serial_unit', 'bit_type',
            'total_pockets', 'total_rows', 'total_columns',
            'evaluation_date', 'evaluation_notes'
        ]
        widgets = {
            'session_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., EVAL-2025-001'
            }),
            'job_card': forms.Select(attrs={'class': 'form-select'}),
            'serial_unit': forms.Select(attrs={'class': 'form-select'}),
            'bit_type': forms.Select(attrs={'class': 'form-select'}),
            'total_pockets': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'total_rows': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 10
            }),
            'total_columns': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 20
            }),
            'evaluation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'evaluation_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this evaluation...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['serial_unit'].required = False
        self.fields['bit_type'].required = False
        self.fields['evaluation_date'].required = False


class EvaluationCellForm(forms.ModelForm):
    """Form for individual cell updates."""

    class Meta:
        model = EvaluationCell
        fields = [
            'pocket_number', 'row', 'column', 'blade_number', 'position_on_blade',
            'evaluation_code', 'feature_code', 'section',
            'condition_description', 'notes', 'wear_percentage'
        ]
        widgets = {
            'pocket_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'row': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'column': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'blade_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'position_on_blade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'evaluation_code': forms.Select(attrs={'class': 'form-select'}),
            'feature_code': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'condition_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Describe condition...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes...'
            }),
            'wear_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': 0,
                'max': 100
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['blade_number'].required = False
        self.fields['position_on_blade'].required = False
        self.fields['feature_code'].required = False
        self.fields['section'].required = False
        self.fields['wear_percentage'].required = False


class ThreadInspectionForm(forms.ModelForm):
    """Form for Thread Inspection."""

    class Meta:
        model = ThreadInspection
        fields = [
            'thread_type', 'thread_size', 'result', 'damage_type',
            'pitch_diameter', 'lead', 'taper',
            'description', 'repair_action'
        ]
        widgets = {
            'thread_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., API REG, IF, FH'
            }),
            'thread_size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 4-1/2 REG'
            }),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'damage_type': forms.Select(attrs={'class': 'form-select'}),
            'pitch_diameter': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001'
            }),
            'lead': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001'
            }),
            'taper': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe any issues found...'
            }),
            'repair_action': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Repair actions taken or required...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['thread_size'].required = False
        self.fields['pitch_diameter'].required = False
        self.fields['lead'].required = False
        self.fields['taper'].required = False


class NDTInspectionForm(forms.ModelForm):
    """Form for NDT (Non-Destructive Testing) Inspection."""

    class Meta:
        model = NDTInspection
        fields = [
            'test_type', 'test_procedure', 'test_area',
            'result', 'defect_severity',
            'defects_found', 'defect_locations', 'recommendations',
            'equipment_used', 'calibration_ref', 'report_number'
        ]
        widgets = {
            'test_type': forms.Select(attrs={'class': 'form-select'}),
            'test_procedure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., ASTM E1417'
            }),
            'test_area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Pin Thread, Body, Gauge Area'
            }),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'defect_severity': forms.Select(attrs={'class': 'form-select'}),
            'defects_found': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List any defects found...'
            }),
            'defect_locations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Describe defect locations...'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommendations for repair or further inspection...'
            }),
            'equipment_used': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Equipment make/model'
            }),
            'calibration_ref': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Calibration reference number'
            }),
            'report_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NDT Report Number'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['test_procedure'].required = False
        self.fields['test_area'].required = False
        self.fields['equipment_used'].required = False
        self.fields['calibration_ref'].required = False
        self.fields['report_number'].required = False


class TechnicalInstructionInstanceForm(forms.Form):
    """Form for accepting/rejecting/overriding technical instructions."""
    action = forms.ChoiceField(
        choices=[
            ('ACCEPT', 'Accept'),
            ('REJECT', 'Reject'),
            ('OVERRIDE', 'Override (Engineer Only)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add notes about this action...'
        })
    )
    override_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for override (required for override action)...'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        override_reason = cleaned_data.get('override_reason')

        if action == 'OVERRIDE' and not override_reason:
            raise forms.ValidationError("Override reason is required when overriding an instruction.")

        return cleaned_data


class RequirementInstanceForm(forms.Form):
    """Form for marking requirements as satisfied."""
    verification_result = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Verification results or evidence...'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional notes...'
        })
    )


class SessionReviewForm(forms.Form):
    """Form for engineer review of evaluation session."""
    review_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Review notes and comments...'
        })
    )
    approval_status = forms.ChoiceField(
        choices=[
            ('APPROVED', 'Approve'),
            ('REJECTED', 'Reject - Request Revision'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class SessionFilterForm(forms.Form):
    """Form for filtering evaluation sessions."""
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(EvaluationSession.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    bit_type = forms.ModelChoiceField(
        queryset=BitType.objects.filter(is_active=True),
        required=False,
        empty_label='All Bit Types',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search session number, job card...'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


# ========== Settings Forms ==========

class BitTypeForm(forms.ModelForm):
    """Form for BitType."""

    class Meta:
        model = BitType
        fields = ['code', 'name', 'description', 'is_active', 'sort_order']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BitSectionForm(forms.ModelForm):
    """Form for BitSection."""

    class Meta:
        model = BitSection
        fields = ['code', 'name', 'description', 'is_active', 'sort_order']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class FeatureCodeForm(forms.ModelForm):
    """Form for FeatureCode."""

    class Meta:
        model = FeatureCode
        fields = ['code', 'name', 'description', 'category', 'is_active', 'sort_order']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CutterEvaluationCodeForm(forms.ModelForm):
    """Form for CutterEvaluationCode."""

    class Meta:
        model = CutterEvaluationCode
        fields = ['code', 'name', 'description', 'color', 'action_required', 'is_active', 'sort_order']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'action_required': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TechnicalInstructionTemplateForm(forms.ModelForm):
    """Form for TechnicalInstructionTemplate."""

    class Meta:
        model = TechnicalInstructionTemplate
        fields = [
            'code', 'title', 'description', 'applies_to_bit_type',
            'applies_to_section', 'priority', 'is_mandatory',
            'requires_engineer_override', 'auto_apply', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'applies_to_bit_type': forms.Select(attrs={'class': 'form-select'}),
            'applies_to_section': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_engineer_override': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_apply': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['applies_to_bit_type'].required = False
        self.fields['applies_to_section'].required = False


class RequirementTemplateForm(forms.ModelForm):
    """Form for RequirementTemplate."""

    class Meta:
        model = RequirementTemplate
        fields = [
            'code', 'title', 'description', 'category',
            'applies_to_bit_type', 'verification_method',
            'is_mandatory', 'auto_apply', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'applies_to_bit_type': forms.Select(attrs={'class': 'form-select'}),
            'verification_method': forms.TextInput(attrs={'class': 'form-control'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_apply': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['applies_to_bit_type'].required = False
        self.fields['verification_method'].required = False
