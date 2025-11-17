"""
Quality Management - Forms
"""
from django import forms
from .models import (
    NonconformanceReport,
    NCRRootCauseAnalysis,
    NCRCorrectiveAction,
    CalibratedEquipment,
    CalibrationRecord,
    QualityDisposition,
)


class NCRForm(forms.ModelForm):
    """Form for creating/editing NCRs."""

    class Meta:
        model = NonconformanceReport
        fields = [
            'ncr_type', 'defect_category', 'title', 'description',
            'detection_point', 'detection_method', 'severity',
            'quantity_affected', 'quantity_contained',
            'customer_impact', 'production_impact', 'safety_impact',
            'job_card_id', 'serial_unit_id', 'batch_order_id',
            'disposition', 'disposition_reason',
            'estimated_cost_impact', 'lost_revenue',
            'assigned_to', 'target_closure_date',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'disposition_reason': forms.Textarea(attrs={'rows': 3}),
            'target_closure_date': forms.DateInput(attrs={'type': 'date'}),
        }


class NCRRootCauseAnalysisForm(forms.ModelForm):
    """Form for adding root cause analysis."""

    class Meta:
        model = NCRRootCauseAnalysis
        fields = [
            'category', 'why_1', 'why_2', 'why_3', 'why_4', 'why_5',
            'root_cause_statement', 'is_systemic'
        ]
        widgets = {
            'why_1': forms.Textarea(attrs={'rows': 2}),
            'why_2': forms.Textarea(attrs={'rows': 2}),
            'why_3': forms.Textarea(attrs={'rows': 2}),
            'why_4': forms.Textarea(attrs={'rows': 2}),
            'why_5': forms.Textarea(attrs={'rows': 2}),
            'root_cause_statement': forms.Textarea(attrs={'rows': 3}),
        }


class NCRCorrectiveActionForm(forms.ModelForm):
    """Form for adding corrective actions."""

    class Meta:
        model = NCRCorrectiveAction
        fields = [
            'action_type', 'description', 'assigned_to', 'due_date'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }


class CalibratedEquipmentForm(forms.ModelForm):
    """Form for calibrated equipment."""

    class Meta:
        model = CalibratedEquipment
        fields = [
            'equipment_id', 'name', 'equipment_type',
            'manufacturer', 'model', 'serial_number',
            'calibration_interval_days', 'calibration_procedure',
            'calibration_standard', 'location', 'custodian',
            'is_critical', 'purchase_date', 'warranty_expiry', 'purchase_cost'
        ]
        widgets = {
            'calibration_procedure': forms.Textarea(attrs={'rows': 3}),
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'type': 'date'}),
        }


class CalibrationRecordForm(forms.ModelForm):
    """Form for recording calibration."""

    class Meta:
        model = CalibrationRecord
        fields = [
            'calibration_date', 'performed_by', 'calibration_lab',
            'certificate_number', 'result', 'adjustments_made',
            'out_of_tolerance_findings', 'measurements_json',
            'next_due_date', 'cost', 'certificate_file'
        ]
        widgets = {
            'calibration_date': forms.DateInput(attrs={'type': 'date'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
            'adjustments_made': forms.Textarea(attrs={'rows': 3}),
            'out_of_tolerance_findings': forms.Textarea(attrs={'rows': 3}),
        }


class QualityDispositionForm(forms.ModelForm):
    """Form for quality disposition."""

    class Meta:
        model = QualityDisposition
        fields = [
            'job_card_id', 'evaluation_session_id', 'decision',
            'inspection_summary', 'deviations_accepted',
            'customer_concession', 'concession_reference',
            'acceptance_template', 'criteria_results_json',
            'customer_name', 'customer_po_number', 'customer_requirements_met',
            'notes', 'ncrs_closed'
        ]
        widgets = {
            'inspection_summary': forms.Textarea(attrs={'rows': 4}),
            'deviations_accepted': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
