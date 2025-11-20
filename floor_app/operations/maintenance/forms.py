"""
Forms for Maintenance module.
"""
from django import forms
from django.utils import timezone
from .models import (
    Asset, AssetCategory, AssetLocation, AssetDocument,
    PMTemplate, PMSchedule, PMTask,
    MaintenanceRequest, WorkOrder, WorkOrderNote, WorkOrderPart,
    DowntimeEvent, ProductionImpact, LostSalesRecord
)


class AssetForm(forms.ModelForm):
    """Form for creating/editing assets."""

    class Meta:
        model = Asset
        fields = [
            'asset_code', 'name', 'description', 'category', 'location',
            'status', 'criticality', 'is_critical',
            'manufacturer', 'model_number', 'serial_number', 'year_manufactured',
            'purchase_date', 'purchase_cost', 'warranty_expires', 'vendor',
            'erp_asset_number', 'installation_date', 'responsible_department',
            'primary_operator', 'meter_reading', 'meter_unit',
            'requires_certification', 'has_safety_lockout',
            'specifications', 'notes'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'specifications': forms.Textarea(attrs={'rows': 4}),
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_expires': forms.DateInput(attrs={'type': 'date'}),
            'installation_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_asset_code(self):
        code = self.cleaned_data['asset_code']
        # Validate format
        if not code.replace('-', '').replace('_', '').isalnum():
            raise forms.ValidationError("Asset code must be alphanumeric (hyphens and underscores allowed)")
        return code.upper()


class AssetCategoryForm(forms.ModelForm):
    """Form for asset categories."""

    class Meta:
        model = AssetCategory
        fields = ['code', 'name', 'description', 'default_criticality', 'default_pm_interval_days', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class AssetLocationForm(forms.ModelForm):
    """Form for asset locations."""

    class Meta:
        model = AssetLocation
        fields = ['code', 'name', 'parent', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class MaintenanceRequestForm(forms.ModelForm):
    """Form for submitting maintenance requests."""

    class Meta:
        model = MaintenanceRequest
        fields = ['asset', 'title', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe the problem, symptoms, or maintenance need...'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Brief title for the request'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Only show active assets
        self.fields['asset'].queryset = Asset.objects.filter(
            is_deleted=False, status__in=['IN_SERVICE', 'UNDER_MAINTENANCE']
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.requested_by = self.user
        if commit:
            instance.save()
        return instance


class RequestReviewForm(forms.ModelForm):
    """Form for reviewing maintenance requests."""

    class Meta:
        model = MaintenanceRequest
        fields = ['status', 'rejection_reason']
        widgets = {
            'rejection_reason': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason')

        if status == 'REJECTED' and not rejection_reason:
            raise forms.ValidationError("Rejection reason is required when rejecting a request")

        return cleaned_data


class WorkOrderForm(forms.ModelForm):
    """Form for creating/editing work orders."""

    class Meta:
        model = WorkOrder
        fields = [
            'asset', 'title', 'problem_description', 'wo_type', 'priority', 'status',
            'planned_start', 'planned_end', 'assigned_to',
            'root_cause_category', 'root_cause_detail',
            'solution_summary', 'actions_taken',
            'labor_cost', 'parts_cost', 'external_cost'
        ]
        widgets = {
            'problem_description': forms.Textarea(attrs={'rows': 4}),
            'solution_summary': forms.Textarea(attrs={'rows': 3}),
            'actions_taken': forms.Textarea(attrs={'rows': 4}),
            'root_cause_detail': forms.Textarea(attrs={'rows': 3}),
            'planned_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'planned_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class WorkOrderAssignForm(forms.ModelForm):
    """Form for assigning work orders."""

    class Meta:
        model = WorkOrder
        fields = ['assigned_to', 'planned_start', 'planned_end']
        widgets = {
            'planned_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'planned_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class WorkOrderCompleteForm(forms.ModelForm):
    """Form for completing work orders."""

    class Meta:
        model = WorkOrder
        fields = [
            'actual_start', 'actual_end', 'actions_taken', 'solution_summary',
            'root_cause_category', 'root_cause_detail', 'follow_up_notes',
            'labor_cost', 'parts_cost', 'external_cost'
        ]
        widgets = {
            'actual_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'actual_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'actions_taken': forms.Textarea(attrs={'rows': 4}),
            'solution_summary': forms.Textarea(attrs={'rows': 3}),
            'root_cause_detail': forms.Textarea(attrs={'rows': 3}),
            'follow_up_notes': forms.Textarea(attrs={'rows': 3}),
        }


class WorkOrderNoteForm(forms.ModelForm):
    """Form for adding notes to work orders."""

    class Meta:
        model = WorkOrderNote
        fields = ['note_type', 'content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Add note or update...'
            }),
        }


class WorkOrderPartForm(forms.ModelForm):
    """Form for adding parts to work orders."""

    class Meta:
        model = WorkOrderPart
        fields = ['part_number', 'part_description', 'quantity_used', 'unit_cost', 'warehouse_location', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class PMTemplateForm(forms.ModelForm):
    """Form for PM templates."""

    class Meta:
        model = PMTemplate
        fields = [
            'code', 'name', 'description', 'instructions', 'safety_notes',
            'tools_required', 'estimated_duration_minutes',
            'frequency_type', 'frequency_days', 'frequency_hours',
            'applies_to_category', 'skill_level_required', 'linked_procedure', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'instructions': forms.Textarea(attrs={'rows': 6}),
            'safety_notes': forms.Textarea(attrs={'rows': 3}),
            'tools_required': forms.Textarea(attrs={'rows': 3}),
        }


class PMTaskForm(forms.ModelForm):
    """Form for PM tasks."""

    class Meta:
        model = PMTask
        fields = ['status', 'scheduled_date', 'notes', 'findings']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'findings': forms.Textarea(attrs={'rows': 3}),
        }


class PMTaskCompleteForm(forms.Form):
    """Form for completing PM tasks."""

    actual_start = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True
    )
    actual_end = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    findings = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Any issues or observations found during PM"
    )
    meter_reading = forms.DecimalField(
        required=False,
        help_text="Current meter reading (if applicable)"
    )
    create_work_order = forms.BooleanField(
        required=False,
        help_text="Create follow-up work order for issues found"
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('actual_start')
        end = cleaned_data.get('actual_end')

        if start and end and end < start:
            raise forms.ValidationError("End time cannot be before start time")

        return cleaned_data


class DowntimeEventForm(forms.ModelForm):
    """Form for recording downtime events."""

    class Meta:
        model = DowntimeEvent
        fields = [
            'asset', 'work_order', 'event_type', 'start_time', 'end_time',
            'is_planned', 'reason_category', 'reason_description', 'severity',
            'has_production_impact', 'notes'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reason_description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if start and end and end < start:
            raise forms.ValidationError("End time cannot be before start time")

        return cleaned_data


class ProductionImpactForm(forms.ModelForm):
    """Form for recording production impact."""

    class Meta:
        model = ProductionImpact
        fields = [
            'downtime_event', 'impact_type', 'batch_reference', 'job_card_number',
            'customer_name', 'product_description',
            'expected_completion_date', 'actual_completion_date', 'delay_minutes',
            'lost_or_delayed_revenue', 'currency', 'is_revenue_confirmed',
            'impact_description', 'notes'
        ]
        widgets = {
            'expected_completion_date': forms.DateInput(attrs={'type': 'date'}),
            'actual_completion_date': forms.DateInput(attrs={'type': 'date'}),
            'impact_description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class LostSalesRecordForm(forms.ModelForm):
    """Form for confirming lost sales."""

    class Meta:
        model = LostSalesRecord
        fields = [
            'production_impact', 'customer_name', 'order_reference',
            'original_order_value', 'revenue_lost', 'revenue_delayed',
            'recovery_possible', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class AssetSearchForm(forms.Form):
    """Form for searching assets."""

    query = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search by code, name, or serial number...'
    }))
    category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories"
    )
    location = forms.ModelChoiceField(
        queryset=AssetLocation.objects.filter(is_active=True),
        required=False,
        empty_label="All Locations"
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Asset.Status.choices),
        required=False
    )
    criticality = forms.ChoiceField(
        choices=[('', 'All Criticalities')] + list(Asset.Criticality.choices),
        required=False
    )


class DateRangeForm(forms.Form):
    """Form for date range filtering."""

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')

        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before start date")

        return cleaned_data
