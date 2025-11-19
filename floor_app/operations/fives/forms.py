"""
5S/Housekeeping Gamification Forms

Forms for 5S audits and improvement actions.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import FiveSAudit, FiveSImprovementAction, FiveSAuditTemplate

User = get_user_model()


class FiveSAuditForm(forms.ModelForm):
    """Form for creating/conducting 5S audits."""

    class Meta:
        model = FiveSAudit
        fields = ['template', 'area_name', 'department', 'building', 'floor_level',
                  'team_name', 'responsible_person', 'audited_by', 'audit_date', 'audit_time']
        widgets = {
            'template': forms.Select(attrs={
                'class': 'form-control',
            }),
            'area_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Production Floor A, Warehouse Zone 1',
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Production, Warehouse, QC',
            }),
            'building': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Building 1, Main Facility',
            }),
            'floor_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Ground Floor, Level 2',
            }),
            'team_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Production Team A',
            }),
            'responsible_person': forms.Select(attrs={
                'class': 'form-control',
            }),
            'audited_by': forms.Select(attrs={
                'class': 'form-control',
            }),
            'audit_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'audit_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
        }
        help_texts = {
            'template': 'Select the audit template to use',
            'area_name': 'Name of the area being audited',
            'department': 'Department responsible for this area',
            'building': 'Building location',
            'floor_level': 'Floor level',
            'team_name': 'Team responsible for maintaining this area',
            'responsible_person': 'Person responsible for this area',
            'audited_by': 'Who is conducting this audit?',
            'audit_date': 'Date of audit',
            'audit_time': 'Time of audit',
        }

    def __init__(self, *args, **kwargs):
        self.auditor = kwargs.pop('auditor', None)
        super().__init__(*args, **kwargs)

        # Only show active templates
        self.fields['template'].queryset = FiveSAuditTemplate.objects.filter(is_active=True)

        # Set audited_by to current user if provided
        if self.auditor:
            self.fields['audited_by'].initial = self.auditor

        # Make area_name required
        self.fields['area_name'].required = True

    def clean(self):
        cleaned_data = super().clean()
        audit_date = cleaned_data.get('audit_date')

        if audit_date:
            from django.utils import timezone
            from datetime import date
            if audit_date > timezone.now().date():
                raise forms.ValidationError({
                    'audit_date': 'Audit date cannot be in the future'
                })

        return cleaned_data


class ImprovementActionForm(forms.ModelForm):
    """Form for creating improvement actions from audits."""

    class Meta:
        model = FiveSImprovementAction
        fields = ['title', 'description', 'category', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title of the improvement action',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed description of what needs to be done...',
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }
        help_texts = {
            'title': 'Clear, concise title for this improvement action',
            'description': 'Detailed description of the improvement needed',
            'category': 'Which of the 5S principles does this address?',
            'assigned_to': 'Who is responsible for completing this action?',
            'due_date': 'When should this be completed by?',
        }

    def __init__(self, *args, **kwargs):
        self.audit = kwargs.pop('audit', None)
        self.assigner = kwargs.pop('assigner', None)
        super().__init__(*args, **kwargs)

        # Filter active users only
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date:
            from django.utils import timezone
            if due_date < timezone.now().date():
                raise forms.ValidationError(
                    'Due date cannot be in the past'
                )
        return due_date

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.audit:
            instance.audit = self.audit
        if self.assigner:
            instance.assigned_by = self.assigner
        if commit:
            instance.save()
        return instance


class ImprovementActionCompletionForm(forms.ModelForm):
    """Form for marking improvement actions as complete."""

    class Meta:
        model = FiveSImprovementAction
        fields = ['completion_notes', 'after_photo']
        widgets = {
            'completion_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what was done to complete this action...',
            }),
            'after_photo': forms.FileInput(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'completion_notes': 'Describe the actions taken and results achieved',
            'after_photo': 'Upload a photo showing the improvement (optional)',
        }

    def clean_completion_notes(self):
        notes = self.cleaned_data.get('completion_notes')
        if not notes or len(notes.strip()) < 10:
            raise forms.ValidationError(
                'Please provide detailed completion notes (at least 10 characters)'
            )
        return notes


class AuditScoringForm(forms.Form):
    """Form for scoring 5S audit items."""

    sort_score = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-100',
        }),
        help_text='Sort (Seiri) - Removing unnecessary items'
    )

    set_in_order_score = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-100',
        }),
        help_text='Set in Order (Seiton) - Organizing items'
    )

    shine_score = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-100',
        }),
        help_text='Shine (Seiso) - Cleaning and maintaining'
    )

    standardize_score = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-100',
        }),
        help_text='Standardize (Seiketsu) - Creating standards'
    )

    sustain_score = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-100',
        }),
        help_text='Sustain (Shitsuke) - Maintaining discipline'
    )

    observations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'General observations...',
        }),
        help_text='Overall observations from the audit'
    )

    strengths = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'What is being done well?',
        }),
        help_text='Strengths and positive practices observed'
    )

    areas_for_improvement = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'What needs improvement?',
        }),
        help_text='Areas that need improvement'
    )

    def clean(self):
        cleaned_data = super().clean()

        # Validate scores are within range
        scores = ['sort_score', 'set_in_order_score', 'shine_score',
                  'standardize_score', 'sustain_score']

        for score_field in scores:
            score = cleaned_data.get(score_field)
            if score is not None and score > 100:
                raise forms.ValidationError({
                    score_field: 'Score cannot exceed 100'
                })

        return cleaned_data
