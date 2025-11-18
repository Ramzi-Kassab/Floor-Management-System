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
            'serial_unit', 'mat_revision', 'job_card', 'batch_order',
            'context', 'customer_name', 'project_name', 'evaluator',
            'general_notes', 'wear_pattern_notes', 'damage_assessment', 'recommendations'
        ]
        widgets = {
            'serial_unit': forms.Select(attrs={'class': 'form-select'}),
            'mat_revision': forms.Select(attrs={'class': 'form-select'}),
            'job_card': forms.Select(attrs={'class': 'form-select'}),
            'batch_order': forms.Select(attrs={'class': 'form-select'}),
            'context': forms.Select(attrs={'class': 'form-select'}),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer name'
            }),
            'project_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Project/Well/Field name'
            }),
            'evaluator': forms.Select(attrs={'class': 'form-select'}),
            'general_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'General notes about this evaluation...'
            }),
            'wear_pattern_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes about observed wear patterns...'
            }),
            'damage_assessment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Overall damage assessment...'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommendations for repair/action...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields optional for easier form entry
        self.fields['job_card'].required = False
        self.fields['batch_order'].required = False
        self.fields['customer_name'].required = False
        self.fields['project_name'].required = False


class EvaluationCellForm(forms.ModelForm):
    """Form for individual cell updates."""

    class Meta:
        model = EvaluationCell
        fields = [
            'blade_number', 'section', 'position_index', 'is_primary',
            'cutter_item', 'cutter_code', 'notes',
            'has_fin_build_up', 'fin_number', 'has_pocket_damage',
            'has_impact_arrestor_issue', 'has_body_build_up',
            'pocket_diameter', 'pocket_depth', 'cutter_exposure',
            'wear_flat_length', 'back_rake_angle', 'side_rake_angle'
        ]
        widgets = {
            'blade_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'position_index': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cutter_item': forms.Select(attrs={'class': 'form-select'}),
            'cutter_code': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes...'
            }),
            'has_fin_build_up': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fin_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'has_pocket_damage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_impact_arrestor_issue': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_body_build_up': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pocket_diameter': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'pocket_depth': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'cutter_exposure': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'wear_flat_length': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'back_rake_angle': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'side_rake_angle': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cutter_item'].required = False
        self.fields['cutter_code'].required = False
        self.fields['fin_number'].required = False
        self.fields['pocket_diameter'].required = False
        self.fields['pocket_depth'].required = False
        self.fields['cutter_exposure'].required = False
        self.fields['wear_flat_length'].required = False
        self.fields['back_rake_angle'].required = False
        self.fields['side_rake_angle'].required = False


class ThreadInspectionForm(forms.ModelForm):
    """Form for Thread Inspection."""

    class Meta:
        model = ThreadInspection
        fields = [
            'thread_type', 'connection_type', 'thread_size', 'result',
            'description', 'thread_crest_condition', 'thread_root_condition',
            'shoulder_condition', 'galling_observed', 'corrosion_observed',
            'repair_recommendation', 'requires_recut', 'requires_replacement',
            'inspected_by'
        ]
        widgets = {
            'thread_type': forms.Select(attrs={'class': 'form-select'}),
            'connection_type': forms.Select(attrs={'class': 'form-select'}),
            'thread_size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 4-1/2 REG'
            }),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe any issues found...'
            }),
            'thread_crest_condition': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Condition of thread crests'
            }),
            'thread_root_condition': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Condition of thread roots'
            }),
            'shoulder_condition': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Condition of thread shoulder'
            }),
            'galling_observed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'corrosion_observed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'repair_recommendation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommended repair actions...'
            }),
            'requires_recut': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_replacement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inspected_by': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['thread_size'].required = False
        self.fields['thread_crest_condition'].required = False
        self.fields['thread_root_condition'].required = False
        self.fields['shoulder_condition'].required = False


class NDTInspectionForm(forms.ModelForm):
    """Form for NDT (Non-Destructive Testing) Inspection."""

    class Meta:
        model = NDTInspection
        fields = [
            'method', 'result', 'areas_inspected', 'indications_description',
            'crack_indications', 'porosity_indications', 'inclusion_indications',
            'max_indication_size', 'indication_count', 'acceptance_standard',
            'meets_acceptance_criteria', 'recommendations', 'requires_retest',
            'equipment_used', 'inspector_certification', 'inspector', 'report_number'
        ]
        widgets = {
            'method': forms.Select(attrs={'class': 'form-select'}),
            'result': forms.Select(attrs={'class': 'form-select'}),
            'areas_inspected': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'e.g., Body, Blades, Shank...'
            }),
            'indications_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of any indications/defects found...'
            }),
            'crack_indications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'porosity_indications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inclusion_indications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_indication_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'mm'
            }),
            'indication_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'acceptance_standard': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., ASME, API, company standard'
            }),
            'meets_acceptance_criteria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommendations based on findings...'
            }),
            'requires_retest': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'equipment_used': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Equipment/instrument used'
            }),
            'inspector_certification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Level II'
            }),
            'inspector': forms.Select(attrs={'class': 'form-select'}),
            'report_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NDT Report Number'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['indications_description'].required = False
        self.fields['max_indication_size'].required = False
        self.fields['acceptance_standard'].required = False
        self.fields['equipment_used'].required = False
        self.fields['inspector_certification'].required = False
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
    context = forms.ChoiceField(
        choices=[('', 'All Contexts')] + list(EvaluationSession.CONTEXT_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search customer, project name...'
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
        fields = ['code', 'name', 'description', 'manufacturer', 'is_active', 'sort_order']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BitSectionForm(forms.ModelForm):
    """Form for BitSection."""

    class Meta:
        model = BitSection
        fields = ['code', 'name', 'description', 'sequence', 'color_code', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sequence': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'color_code': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FeatureCodeForm(forms.ModelForm):
    """Form for FeatureCode."""

    class Meta:
        model = FeatureCode
        fields = ['code', 'name', 'description', 'geometry_type', 'color_code', 'is_active', 'sort_order']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'geometry_type': forms.Select(attrs={'class': 'form-select'}),
            'color_code': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CutterEvaluationCodeForm(forms.ModelForm):
    """Form for CutterEvaluationCode."""

    class Meta:
        model = CutterEvaluationCode
        fields = ['code', 'name', 'description', 'action', 'color_code', 'is_active', 'sort_order']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'action': forms.Select(attrs={'class': 'form-select'}),
            'color_code': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TechnicalInstructionTemplateForm(forms.ModelForm):
    """Form for TechnicalInstructionTemplate."""

    class Meta:
        model = TechnicalInstructionTemplate
        fields = [
            'code', 'name', 'description', 'scope', 'stage', 'severity',
            'output_template', 'auto_generate', 'requires_acknowledgment',
            'can_be_overridden', 'override_requires_approval', 'priority', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'scope': forms.Select(attrs={'class': 'form-select'}),
            'stage': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'output_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'auto_generate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_acknowledgment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_be_overridden': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'override_requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RequirementTemplateForm(forms.ModelForm):
    """Form for RequirementTemplate."""

    class Meta:
        model = RequirementTemplate
        fields = [
            'code', 'name', 'description', 'stage', 'requirement_type',
            'is_mandatory', 'can_be_waived', 'waiver_authority',
            'satisfaction_instructions', 'lead_time_hours', 'sort_order', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stage': forms.Select(attrs={'class': 'form-select'}),
            'requirement_type': forms.Select(attrs={'class': 'form-select'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_be_waived': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'waiver_authority': forms.TextInput(attrs={'class': 'form-control'}),
            'satisfaction_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'lead_time_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['waiver_authority'].required = False
        self.fields['satisfaction_instructions'].required = False
