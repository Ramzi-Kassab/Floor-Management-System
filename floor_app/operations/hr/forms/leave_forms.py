"""
Leave Management Forms
Comprehensive forms for leave policies, balances, and requests
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from floor_app.operations.hr.models import (
    LeavePolicy, LeaveBalance, LeaveRequest,
    LeaveType, LeaveRequestStatus
)


class LeavePolicyForm(forms.ModelForm):
    """Form for creating/editing leave policies"""

    class Meta:
        model = LeavePolicy
        fields = [
            'name', 'code', 'leave_type', 'description',
            'annual_entitlement_days', 'max_accumulation_days',
            'carry_forward_days', 'carry_forward_expiry_months',
            'minimum_notice_days', 'maximum_consecutive_days',
            'minimum_days_per_request', 'accrual_type',
            'prorate_for_new_joiners', 'prorate_for_leavers',
            'requires_approval', 'auto_approve_below_days',
            'requires_medical_certificate', 'medical_certificate_after_days',
            'allows_encashment', 'max_encashment_days',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'annual_entitlement_days': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'max_accumulation_days': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'carry_forward_days': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'carry_forward_expiry_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_notice_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'maximum_consecutive_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_days_per_request': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'accrual_type': forms.Select(attrs={'class': 'form-select'}),
            'prorate_for_new_joiners': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prorate_for_leavers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_approve_below_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'requires_medical_certificate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'medical_certificate_after_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'allows_encashment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_encashment_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LeaveBalanceForm(forms.ModelForm):
    """Form for adjusting leave balances"""

    class Meta:
        model = LeaveBalance
        fields = [
            'employee', 'leave_policy', 'year',
            'opening_balance', 'adjustment', 'adjustment_reason'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'leave_policy': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'adjustment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'adjustment_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_adjustment(self):
        """Ensure adjustment has a reason if non-zero"""
        adjustment = self.cleaned_data.get('adjustment')
        adjustment_reason = self.cleaned_data.get('adjustment_reason')

        if adjustment and adjustment != 0 and not adjustment_reason:
            raise ValidationError('Please provide a reason for the balance adjustment.')

        return adjustment


class LeaveRequestForm(forms.ModelForm):
    """Form for creating leave requests"""

    class Meta:
        model = LeaveRequest
        fields = [
            'employee', 'leave_policy', 'start_date', 'end_date',
            'is_half_day_start', 'is_half_day_end',
            'reason', 'contact_during_leave',
            'coverage_employee_id', 'handover_notes',
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'leave_policy': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_half_day_start': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_half_day_end': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_during_leave': forms.TextInput(attrs={'class': 'form-control'}),
            'coverage_employee_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'handover_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # If creating new request, set employee to current user's employee record
        if not self.instance.pk and self.user:
            from floor_app.operations.hr.models import HREmployee
            try:
                employee = HREmployee.objects.get(user=self.user, is_deleted=False)
                self.fields['employee'].initial = employee
                self.fields['employee'].widget = forms.HiddenInput()
            except HREmployee.DoesNotExist:
                pass

    def clean(self):
        """Validate leave request"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        leave_policy = cleaned_data.get('leave_policy')
        employee = cleaned_data.get('employee')
        is_half_day_start = cleaned_data.get('is_half_day_start')
        is_half_day_end = cleaned_data.get('is_half_day_end')

        if not all([start_date, end_date, leave_policy, employee]):
            return cleaned_data

        # Validate dates
        if start_date > end_date:
            raise ValidationError('End date must be after start date.')

        # Check if dates are in the past
        if start_date < timezone.now().date():
            raise ValidationError('Cannot request leave for past dates.')

        # Calculate total days
        total_days = (end_date - start_date).days + 1

        # Adjust for half days
        if is_half_day_start:
            total_days -= 0.5
        if is_half_day_end:
            total_days -= 0.5

        cleaned_data['total_days'] = Decimal(str(total_days))

        # Check minimum notice
        if leave_policy.minimum_notice_days > 0:
            notice_days = (start_date - timezone.now().date()).days
            if notice_days < leave_policy.minimum_notice_days:
                raise ValidationError(
                    f'This leave type requires at least {leave_policy.minimum_notice_days} days notice.'
                )

        # Check maximum consecutive days
        if total_days > leave_policy.maximum_consecutive_days:
            raise ValidationError(
                f'Maximum consecutive days for this leave type is {leave_policy.maximum_consecutive_days}.'
            )

        # Check minimum days per request
        if total_days < float(leave_policy.minimum_days_per_request):
            raise ValidationError(
                f'Minimum request for this leave type is {leave_policy.minimum_days_per_request} days.'
            )

        # Check available balance
        try:
            balance = LeaveBalance.objects.get(
                employee=employee,
                leave_policy=leave_policy,
                year=start_date.year
            )
            if balance.available_balance < total_days:
                raise ValidationError(
                    f'Insufficient leave balance. Available: {balance.available_balance} days, Requested: {total_days} days.'
                )
        except LeaveBalance.DoesNotExist:
            raise ValidationError(
                f'No leave balance found for {leave_policy.name} in {start_date.year}. Please contact HR.'
            )

        # Check for overlapping requests
        overlapping = LeaveRequest.objects.filter(
            employee=employee,
            status__in=[LeaveRequestStatus.PENDING_APPROVAL, LeaveRequestStatus.APPROVED]
        ).filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        )

        if self.instance.pk:
            overlapping = overlapping.exclude(pk=self.instance.pk)

        if overlapping.exists():
            raise ValidationError('You have an overlapping leave request for these dates.')

        return cleaned_data

    def save(self, commit=True):
        """Save leave request and generate request number"""
        instance = super().save(commit=False)

        # Generate request number if new
        if not instance.pk:
            instance.request_number = LeaveRequest.generate_request_number()
            instance.status = LeaveRequestStatus.DRAFT

        # Set total days from cleaned data
        if hasattr(self, 'cleaned_data') and 'total_days' in self.cleaned_data:
            instance.total_days = self.cleaned_data['total_days']

        if commit:
            instance.save()

        return instance


class LeaveRequestApprovalForm(forms.Form):
    """Form for approving/rejecting leave requests"""
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text='Optional notes (required for rejection)'
    )

    def clean(self):
        """Ensure notes are provided for rejection"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        notes = cleaned_data.get('notes')

        if action == 'reject' and not notes:
            raise ValidationError('Please provide a reason for rejection.')

        return cleaned_data


class LeaveRequestSearchForm(forms.Form):
    """Form for searching/filtering leave requests"""
    employee = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='All Employees'
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + LeaveRequestStatus.CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    leave_type = forms.ChoiceField(
        choices=[('', 'All Leave Types')] + LeaveType.CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from floor_app.operations.hr.models import HREmployee
        self.fields['employee'].queryset = HREmployee.objects.filter(
            is_deleted=False
        ).select_related('user').order_by('employee_no')
