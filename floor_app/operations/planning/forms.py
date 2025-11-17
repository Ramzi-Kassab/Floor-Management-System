"""
Planning & KPI Management - Forms
"""
from django import forms
from .models import (
    ResourceType,
    ResourceCapacity,
    ProductionSchedule,
    ScheduledOperation,
    KPIDefinition,
    KPIValue,
)


class ResourceTypeForm(forms.ModelForm):
    """Form for resource type."""

    class Meta:
        model = ResourceType
        fields = [
            'code', 'name', 'description', 'category', 'department',
            'default_capacity_per_shift', 'efficiency_factor',
            'setup_time_minutes', 'min_batch_size',
            'is_bottleneck', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ResourceCapacityForm(forms.ModelForm):
    """Form for resource capacity planning."""

    class Meta:
        model = ResourceCapacity
        fields = [
            'date', 'shift', 'available_hours', 'reserved_hours',
            'planned_load_hours', 'actual_load_hours', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class ProductionScheduleForm(forms.ModelForm):
    """Form for production schedule."""

    class Meta:
        model = ProductionSchedule
        fields = [
            'name', 'schedule_date', 'planning_horizon_days',
            'scheduling_algorithm', 'priority_weighting', 'notes'
        ]
        widgets = {
            'schedule_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ScheduledOperationForm(forms.ModelForm):
    """Form for scheduled operation."""

    class Meta:
        model = ScheduledOperation
        fields = [
            'job_card_id', 'job_route_step_id', 'operation_code',
            'planned_start', 'planned_end', 'planned_duration_hours',
            'resource_type', 'assigned_asset_id', 'assigned_employee_id',
            'sequence_number', 'priority_score',
            'earliest_start', 'latest_end',
            'materials_available', 'materials_shortage_list'
        ]
        widgets = {
            'planned_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'planned_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'earliest_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'latest_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'materials_shortage_list': forms.Textarea(attrs={'rows': 2}),
        }


class KPIDefinitionForm(forms.ModelForm):
    """Form for KPI definition."""

    class Meta:
        model = KPIDefinition
        fields = [
            'code', 'name', 'description', 'category', 'unit',
            'calculation_method', 'aggregation_period',
            'target_value', 'warning_threshold', 'critical_threshold',
            'higher_is_better', 'decimal_places',
            'display_order', 'show_on_dashboard', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'calculation_method': forms.Textarea(attrs={'rows': 4}),
        }


class KPIValueForm(forms.ModelForm):
    """Form for recording KPI values."""

    class Meta:
        model = KPIValue
        fields = [
            'kpi_definition', 'period_start', 'period_end', 'value',
            'job_card_id', 'batch_order_id', 'customer_name',
            'employee_id', 'asset_id', 'department', 'notes'
        ]
        widgets = {
            'period_start': forms.DateInput(attrs={'type': 'date'}),
            'period_end': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
