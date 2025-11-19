"""
Retrieval System Forms

Forms for creating retrieval requests and supervisor approvals.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import RetrievalRequest


class RetrievalRequestForm(forms.ModelForm):
    """
    Form for creating a retrieval request.
    """

    class Meta:
        model = RetrievalRequest
        fields = ['action_type', 'reason']
        widgets = {
            'action_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please provide a detailed reason for this retrieval request...',
                'required': True
            })
        }
        labels = {
            'action_type': 'Action Type',
            'reason': 'Reason for Retrieval'
        }
        help_texts = {
            'action_type': 'Select the type of retrieval action you need',
            'reason': 'Explain why you need to retrieve/undo this action. Be specific and detailed.'
        }

    def clean_reason(self):
        """Validate that reason is not empty and has minimum length."""
        reason = self.cleaned_data.get('reason', '').strip()

        if not reason:
            raise ValidationError('Reason is required.')

        if len(reason) < 10:
            raise ValidationError('Reason must be at least 10 characters long.')

        return reason


class SupervisorApprovalForm(forms.Form):
    """
    Form for supervisor to approve or reject a retrieval request.
    """

    DECISION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        required=True,
        label='Decision'
    )

    comments = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional comments about your decision...'
        }),
        required=False,
        label='Comments',
        help_text='Optional: Provide additional context for your decision'
    )

    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Please provide a reason for rejection...'
        }),
        required=False,
        label='Rejection Reason',
        help_text='Required if rejecting the request'
    )

    def clean(self):
        """Validate that rejection reason is provided if rejecting."""
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        rejection_reason = cleaned_data.get('rejection_reason', '').strip()

        if decision == 'reject' and not rejection_reason:
            raise ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a request.'
            })

        return cleaned_data


class RetrievalFilterForm(forms.Form):
    """
    Form for filtering retrieval requests in dashboards.
    """

    STATUS_CHOICES = [('', 'All Statuses')] + list(RetrievalRequest.STATUS_CHOICES)
    ACTION_CHOICES = [('', 'All Actions')] + list(RetrievalRequest.ACTION_TYPE_CHOICES)

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm'
        }),
        label='Status'
    )

    action_type = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm'
        }),
        label='Action Type'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date'
        }),
        label='From Date'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date'
        }),
        label='To Date'
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Search by reason or object...'
        }),
        label='Search'
    )


class BulkApprovalForm(forms.Form):
    """
    Form for bulk approval/rejection of retrieval requests.
    """

    request_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve Selected'),
            ('reject', 'Reject Selected'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True,
        label='Action'
    )

    bulk_rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for bulk rejection...'
        }),
        required=False,
        label='Rejection Reason',
        help_text='Required for bulk rejection'
    )

    def clean_request_ids(self):
        """Parse and validate request IDs."""
        ids_str = self.cleaned_data.get('request_ids', '')

        try:
            ids = [int(id_str.strip()) for id_str in ids_str.split(',') if id_str.strip()]
        except ValueError:
            raise ValidationError('Invalid request IDs.')

        if not ids:
            raise ValidationError('No requests selected.')

        return ids

    def clean(self):
        """Validate bulk rejection reason."""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('bulk_rejection_reason', '').strip()

        if action == 'reject' and not rejection_reason:
            raise ValidationError({
                'bulk_rejection_reason': 'Rejection reason is required for bulk rejection.'
            })

        return cleaned_data
