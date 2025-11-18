"""
Employee Document Management Forms
Separate forms for Employee self-service and HR administration
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from floor_app.operations.hr.models import (
    EmployeeDocument, DocumentRenewal, ExpiryAlert,
    DocumentType, DocumentStatus
)


# ============================================================================
# EMPLOYEE FORMS (Self-Service)
# ============================================================================

class EmployeeDocumentUploadForm(forms.ModelForm):
    """
    Simple form for employees to upload their own documents
    """
    file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
        }),
        help_text='Accepted formats: PDF, JPG, PNG, DOC, DOCX (Max 10MB)'
    )

    class Meta:
        model = EmployeeDocument
        fields = [
            'document_type', 'title', 'document_number',
            'description', 'issue_date', 'expiry_date',
            'issuing_authority', 'issuing_country', 'notes'
        ]
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Medical Certificate for Sick Leave'
            }),
            'document_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document reference number (if any)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the document'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'issuing_authority': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Ministry of Health'
            }),
            'issuing_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Saudi Arabia'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any additional notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)

        # Make certain fields optional for employee upload
        self.fields['document_number'].required = False
        self.fields['description'].required = False
        self.fields['issue_date'].required = False
        self.fields['expiry_date'].required = False
        self.fields['issuing_authority'].required = False
        self.fields['issuing_country'].required = False
        self.fields['notes'].required = False

    def clean_file(self):
        """Validate file upload"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must not exceed 10MB.')

            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            file_ext = file.name.lower().split('.')[-1]
            if f'.{file_ext}' not in allowed_extensions:
                raise ValidationError(f'File type .{file_ext} is not allowed.')

        return file

    def save(self, commit=True):
        """Save document with employee and file info"""
        instance = super().save(commit=False)

        if self.employee:
            instance.employee = self.employee

        # Handle file upload
        file = self.cleaned_data.get('file')
        if file:
            instance.file_name = file.name
            instance.file_size_bytes = file.size
            instance.file_type = file.content_type
            # File path will be set by the view after saving to storage
            instance.file_path = f'employee_documents/{self.employee.id}/{file.name}'

        # Set default status
        instance.status = DocumentStatus.VALID

        if commit:
            instance.save()

        return instance


class DocumentRenewalRequestForm(forms.ModelForm):
    """
    Form for employees to request document renewal
    """
    class Meta:
        model = DocumentRenewal
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Please provide any details about the renewal request...'
            })
        }

    def save(self, document, commit=True):
        """Save renewal request"""
        instance = super().save(commit=False)
        instance.document = document
        instance.status = 'REQUESTED'

        if commit:
            instance.save()

        return instance


# ============================================================================
# HR FORMS (Administrative)
# ============================================================================

class HRDocumentForm(forms.ModelForm):
    """
    Comprehensive form for HR to manage employee documents
    Includes all fields including administrative controls
    """
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
        }),
        help_text='Upload new file (leave empty to keep existing)'
    )

    class Meta:
        model = EmployeeDocument
        fields = [
            'employee', 'document_type', 'title', 'document_number',
            'description', 'status', 'issue_date', 'expiry_date',
            'renewal_reminder_days', 'issuing_authority', 'issuing_country',
            'is_verified', 'verification_notes', 'is_confidential',
            'access_restricted', 'is_mandatory', 'compliance_category',
            'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'renewal_reminder_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'issuing_authority': forms.TextInput(attrs={'class': 'form-control'}),
            'issuing_country': forms.TextInput(attrs={'class': 'form-control'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'verification_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_confidential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'access_restricted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'compliance_category': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_file(self):
        """Validate file upload"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (20MB limit for HR)
            if file.size > 20 * 1024 * 1024:
                raise ValidationError('File size must not exceed 20MB.')

        return file


class DocumentSearchForm(forms.Form):
    """
    Advanced search form for HR to filter documents
    """
    employee = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Employees'
    )
    document_type = forms.ChoiceField(
        choices=[('', 'All Document Types')] + DocumentType.CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + DocumentStatus.CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    expiry_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Expiry From'
    )
    expiry_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Expiry To'
    )
    expiring_within_days = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 30'}),
        label='Expiring Within (Days)',
        help_text='Show documents expiring within specified days'
    )
    is_verified = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Verified Only'), ('false', 'Unverified Only')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Verification Status'
    )
    is_mandatory = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Mandatory Only'), ('false', 'Optional Only')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mandatory Documents'
    )
    search_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, document number, or notes...'
        }),
        label='Search Text'
    )
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Departments',
        label='Department'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from floor_app.operations.hr.models import HREmployee, Department

        # Set queryset for employee
        self.fields['employee'].queryset = HREmployee.objects.filter(
            is_deleted=False
        ).select_related('user').order_by('employee_no')

        # Set queryset for department
        self.fields['department'].queryset = Department.objects.all().order_by('name')


class DocumentVerificationForm(forms.Form):
    """
    Form for HR to verify/approve employee documents
    """
    is_verified = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    verification_notes = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter verification notes or rejection reason...'
        }),
        label='Verification Notes'
    )


class BulkDocumentActionForm(forms.Form):
    """
    Form for bulk actions on documents
    """
    action = forms.ChoiceField(
        choices=[
            ('', 'Select Action'),
            ('verify', 'Mark as Verified'),
            ('archive', 'Archive Documents'),
            ('delete', 'Delete Documents'),
            ('export', 'Export to Excel'),
            ('send_reminder', 'Send Expiry Reminders'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Bulk Action'
    )
    document_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes for this action...'
        }),
        label='Notes'
    )


class ExpiryAlertForm(forms.ModelForm):
    """
    Form for managing expiry alerts
    """
    class Meta:
        model = ExpiryAlert
        fields = ['action_taken', 'acknowledged']
        widgets = {
            'action_taken': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Describe action taken...'
            }),
            'acknowledged': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
