"""
Vendor Portal Forms

Forms for vendor registration, RFQs, and quotations.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import Vendor, RFQ, Quotation, PurchaseOrder

User = get_user_model()


class VendorRegistrationForm(forms.ModelForm):
    """Form for vendor registration/self-signup."""

    class Meta:
        model = Vendor
        fields = ['company_name', 'legal_name', 'registration_number', 'tax_id',
                  'contact_person', 'contact_email', 'contact_phone', 'website',
                  'address', 'city', 'state', 'country', 'postal_code',
                  'categories', 'specializations']
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company/Business name',
            }),
            'legal_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Legal registered name',
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business registration number',
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax ID / VAT number',
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact person name',
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@company.com',
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+971 50 123 4567',
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.company.com',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Full business address',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Province/Emirate',
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal/ZIP code',
            }),
            'categories': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Product/service categories (comma-separated)',
            }),
            'specializations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe your specializations and capabilities...',
            }),
        }
        help_texts = {
            'company_name': 'Trading/business name',
            'legal_name': 'Official registered legal name',
            'categories': 'Product or service categories you provide',
            'specializations': 'Your areas of specialization',
        }

    def clean_contact_email(self):
        email = self.cleaned_data.get('contact_email')
        # Check if email already exists (only for new vendors)
        if not self.instance.pk:
            if Vendor.objects.filter(contact_email=email).exists():
                raise forms.ValidationError(
                    'A vendor with this email is already registered'
                )
        return email


class VendorUpdateForm(forms.ModelForm):
    """Form for vendors to update their profile."""

    class Meta:
        model = Vendor
        fields = ['contact_person', 'contact_email', 'contact_phone', 'website',
                  'address', 'city', 'state', 'country', 'postal_code',
                  'categories', 'specializations', 'bank_name', 'account_number']
        widgets = {
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'categories': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'specializations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class RFQForm(forms.ModelForm):
    """Form for creating Request for Quotations."""

    class Meta:
        model = RFQ
        fields = ['title', 'description', 'department', 'project',
                  'submission_deadline', 'required_delivery_date', 'priority',
                  'invited_vendors', 'published_publicly', 'payment_terms',
                  'delivery_terms', 'warranty_requirements', 'special_requirements']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Office Furniture for New Building',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed description of requirements...',
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Purchasing, Production',
            }),
            'project': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Project name (if applicable)',
            }),
            'submission_deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'required_delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control',
            }),
            'invited_vendors': forms.SelectMultiple(attrs={
                'class': 'form-control',
            }),
            'published_publicly': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'payment_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'e.g., Net 30 days, 50% advance',
            }),
            'delivery_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Delivery terms and conditions...',
            }),
            'warranty_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Warranty requirements...',
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any special requirements...',
            }),
        }
        help_texts = {
            'title': 'Brief title for this RFQ',
            'description': 'Detailed description of what you need',
            'submission_deadline': 'Deadline for vendors to submit quotations',
            'required_delivery_date': 'When do you need the items/services?',
            'invited_vendors': 'Invite specific vendors',
            'published_publicly': 'Allow all registered vendors to submit quotations',
        }

    def __init__(self, *args, **kwargs):
        self.requested_by = kwargs.pop('requested_by', None)
        super().__init__(*args, **kwargs)

        # Only show approved/active vendors
        self.fields['invited_vendors'].queryset = Vendor.objects.filter(
            status__in=['APPROVED', 'ACTIVE']
        )

    def clean(self):
        cleaned_data = super().clean()
        submission_deadline = cleaned_data.get('submission_deadline')
        required_delivery_date = cleaned_data.get('required_delivery_date')

        # Validate submission deadline is in future
        if submission_deadline:
            from django.utils import timezone
            if submission_deadline < timezone.now():
                raise forms.ValidationError({
                    'submission_deadline': 'Submission deadline must be in the future'
                })

        # Validate delivery date is after submission deadline
        if submission_deadline and required_delivery_date:
            if required_delivery_date <= submission_deadline.date():
                raise forms.ValidationError({
                    'required_delivery_date': 'Required delivery date should be after submission deadline'
                })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.requested_by:
            instance.requested_by = self.requested_by

        # Set issue date
        if not instance.issue_date:
            from django.utils import timezone
            instance.issue_date = timezone.now().date()

        if commit:
            instance.save()
            # Save many-to-many relationships
            self.save_m2m()
        return instance


class QuotationForm(forms.ModelForm):
    """Form for vendors to submit quotations."""

    class Meta:
        model = Quotation
        fields = ['subtotal', 'tax_amount', 'shipping_cost', 'total_amount', 'currency',
                  'payment_terms', 'delivery_timeframe', 'warranty', 'validity_days']
        widgets = {
            'subtotal': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'shipping_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'USD',
            }),
            'payment_terms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Your payment terms...',
            }),
            'delivery_timeframe': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2 weeks, 30 days',
            }),
            'warranty': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Warranty terms...',
            }),
            'validity_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '30',
            }),
        }
        help_texts = {
            'subtotal': 'Subtotal before tax and shipping',
            'tax_amount': 'Tax/VAT amount',
            'shipping_cost': 'Shipping/delivery cost',
            'total_amount': 'Total amount',
            'validity_days': 'How many days is this quotation valid?',
        }

    def __init__(self, *args, **kwargs):
        self.rfq = kwargs.pop('rfq', None)
        self.vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        subtotal = cleaned_data.get('subtotal')
        tax_amount = cleaned_data.get('tax_amount')
        shipping_cost = cleaned_data.get('shipping_cost')
        total_amount = cleaned_data.get('total_amount')

        # Validate total calculation
        if all([subtotal is not None, tax_amount is not None,
                shipping_cost is not None, total_amount is not None]):
            calculated_total = subtotal + tax_amount + shipping_cost
            if abs(float(calculated_total) - float(total_amount)) > 0.01:
                raise forms.ValidationError({
                    'total_amount': f'Total should be {calculated_total:.2f} (subtotal + tax + shipping)'
                })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.rfq:
            instance.rfq = self.rfq
        if self.vendor:
            instance.vendor = self.vendor
        if commit:
            instance.save()
        return instance


class QuotationEvaluationForm(forms.ModelForm):
    """Form for evaluating vendor quotations."""

    class Meta:
        model = Quotation
        fields = ['technical_score', 'commercial_score', 'overall_score',
                  'evaluation_notes', 'status']
        widgets = {
            'technical_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0-100',
                'step': '0.01',
            }),
            'commercial_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0-100',
                'step': '0.01',
            }),
            'overall_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0-100',
                'step': '0.01',
            }),
            'evaluation_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Evaluation notes and comments...',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        help_texts = {
            'technical_score': 'Technical evaluation score (0-100)',
            'commercial_score': 'Commercial/pricing evaluation score (0-100)',
            'overall_score': 'Overall evaluation score (0-100)',
            'evaluation_notes': 'Evaluation notes',
        }

    def __init__(self, *args, **kwargs):
        self.evaluator = kwargs.pop('evaluator', None)
        super().__init__(*args, **kwargs)

        # Limit status choices
        status_choices = [
            ('UNDER_REVIEW', 'Under Review'),
            ('SHORTLISTED', 'Shortlisted'),
            ('ACCEPTED', 'Accepted'),
            ('REJECTED', 'Rejected'),
        ]
        self.fields['status'].choices = status_choices

    def clean(self):
        cleaned_data = super().clean()
        technical_score = cleaned_data.get('technical_score')
        commercial_score = cleaned_data.get('commercial_score')
        overall_score = cleaned_data.get('overall_score')

        # Validate scores are within range
        for score_name, score_value in [
            ('technical_score', technical_score),
            ('commercial_score', commercial_score),
            ('overall_score', overall_score)
        ]:
            if score_value is not None:
                if score_value < 0 or score_value > 100:
                    raise forms.ValidationError({
                        score_name: 'Score must be between 0 and 100'
                    })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.evaluator:
            instance.evaluated_by = self.evaluator
            from django.utils import timezone
            instance.evaluation_date = timezone.now().date()
        if commit:
            instance.save()
        return instance


class VendorApprovalForm(forms.ModelForm):
    """Form for approving vendor registrations."""

    class Meta:
        model = Vendor
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Approval/rejection notes...',
            }),
        }
        help_texts = {
            'status': 'Approve or reject vendor registration',
            'notes': 'Notes about approval decision',
        }

    def __init__(self, *args, **kwargs):
        self.approver = kwargs.pop('approver', None)
        super().__init__(*args, **kwargs)

        # Limit status choices
        status_choices = [
            ('APPROVED', 'Approved'),
            ('ACTIVE', 'Active'),
            ('SUSPENDED', 'Suspended'),
            ('BLACKLISTED', 'Blacklisted'),
        ]
        self.fields['status'].choices = status_choices

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.approver and instance.status in ['APPROVED', 'ACTIVE']:
            instance.approved_by = self.approver
            from django.utils import timezone
            instance.approval_date = timezone.now().date()
        if commit:
            instance.save()
        return instance
