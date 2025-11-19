"""
Approval Workflow System Forms

Forms for creating and managing approval requests and delegations.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import ApprovalRequest, ApprovalDelegation, ApprovalWorkflow

User = get_user_model()


class ApprovalRequestForm(forms.ModelForm):
    """Form for creating approval requests."""

    class Meta:
        model = ApprovalRequest
        fields = ['workflow', 'title', 'description', 'due_at', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter approval request title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what needs approval...',
            }),
            'workflow': forms.Select(attrs={
                'class': 'form-control',
            }),
            'due_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'title': 'Brief title describing the approval request',
            'description': 'Detailed description of what needs to be approved and why',
            'workflow': 'Select the appropriate approval workflow',
            'due_at': 'When do you need this approval by?',
            'priority': 'Set priority level for this request',
        }

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester', None)
        super().__init__(*args, **kwargs)

        # Only show active workflows
        self.fields['workflow'].queryset = ApprovalWorkflow.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        due_at = cleaned_data.get('due_at')

        if due_at:
            from django.utils import timezone
            if due_at <= timezone.now():
                raise forms.ValidationError({
                    'due_at': 'Due date must be in the future'
                })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.requester:
            instance.requester = self.requester
        if commit:
            instance.save()
        return instance


class DelegationForm(forms.ModelForm):
    """Form for creating approval delegations."""

    delegate_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text='Select the user to delegate your approvals to'
    )

    class Meta:
        model = ApprovalDelegation
        fields = ['delegate_to', 'start_date', 'end_date', 'reason', 'workflow_types']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for delegation (e.g., on leave, out of office)',
            }),
            'workflow_types': forms.SelectMultiple(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'start_date': 'When should the delegation start?',
            'end_date': 'When should the delegation end?',
            'reason': 'Explain why you are delegating (optional)',
            'workflow_types': 'Leave empty to delegate all approval types',
        }

    def __init__(self, *args, **kwargs):
        self.delegator = kwargs.pop('delegator', None)
        super().__init__(*args, **kwargs)

        # Exclude self from delegate options
        if self.delegator:
            self.fields['delegate_to'].queryset = User.objects.filter(
                is_active=True
            ).exclude(id=self.delegator.id)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        delegate_to = cleaned_data.get('delegate_to')

        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError({
                    'end_date': 'End date must be after start date'
                })

        if delegate_to and self.delegator:
            if delegate_to == self.delegator:
                raise forms.ValidationError({
                    'delegate_to': 'You cannot delegate to yourself'
                })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.delegator:
            instance.delegator = self.delegator
        if commit:
            instance.save()
        return instance


class ApprovalActionForm(forms.Form):
    """Form for approving or rejecting approval requests."""

    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        initial='approve',
    )

    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add comments (optional for approval, required for rejection)',
        }),
        help_text='Provide comments or reasons for your decision'
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        comments = cleaned_data.get('comments')

        if action == 'reject' and not comments:
            raise forms.ValidationError({
                'comments': 'Comments are required when rejecting a request'
            })

        return cleaned_data
