"""
Sales, Lifecycle & Drilling Operations - Forms
"""
from django import forms
from .models import (
    Customer, Rig, Well,
    SalesOpportunity, SalesOrder, SalesOrderLine,
    DrillingRun,
    DullGradeEvaluation,
    BitLifecycleEvent, Shipment, JunkSale,
)


# ============================================================================
# Customer Management Forms
# ============================================================================

class CustomerForm(forms.ModelForm):
    """Form for customer management."""

    class Meta:
        model = Customer
        fields = [
            'customer_code', 'name', 'legal_name', 'customer_type',
            'account_status', 'parent_company', 'is_billing_entity',
            'is_operating_entity', 'billing_customer',
            'primary_contact_name', 'primary_contact_email',
            'primary_contact_phone', 'address', 'country', 'city',
            'payment_terms_days', 'credit_limit', 'currency',
            'requires_coc', 'requires_dull_grade', 'custom_report_format',
            'external_id', 'notes'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class RigForm(forms.ModelForm):
    """Form for rig management."""

    class Meta:
        model = Rig
        fields = [
            'rig_code', 'name', 'rig_type', 'status',
            'owner_customer', 'operator_customer', 'drilling_contractor',
            'max_depth_ft', 'top_drive', 'mud_pump_capacity',
            'current_location', 'gps_coordinates',
            'rig_manager', 'toolpusher', 'contact_phone',
            'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class WellForm(forms.ModelForm):
    """Form for well management."""

    class Meta:
        model = Well
        fields = [
            'well_name', 'uwi', 'api_number', 'well_type', 'status',
            'operator_customer', 'current_rig', 'field_name',
            'block_name', 'country',
            'gps_latitude', 'gps_longitude',
            'spud_date', 'planned_td_ft', 'current_depth_ft',
            'notes'
        ]
        widgets = {
            'spud_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


# ============================================================================
# Sales Management Forms
# ============================================================================

class SalesOpportunityForm(forms.ModelForm):
    """Form for sales opportunity/forecast."""

    class Meta:
        model = SalesOpportunity
        fields = [
            'name', 'description', 'customer', 'well', 'rig', 'field_name',
            'bit_size_inches', 'bit_type', 'mat_number', 'quantity', 'application',
            'status', 'probability', 'estimated_value', 'currency',
            'expected_order_date', 'expected_delivery_date',
            'sales_rep', 'closed_date', 'close_reason', 'competitor',
            'converted_to_order', 'notes'
        ]
        widgets = {
            'expected_order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'closed_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'close_reason': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class SalesOrderForm(forms.ModelForm):
    """Form for sales order."""

    class Meta:
        model = SalesOrder
        fields = [
            'customer', 'customer_po_number', 'billing_customer',
            'well', 'rig', 'delivery_location', 'status', 'priority',
            'order_date', 'required_delivery_date', 'promised_delivery_date',
            'actual_delivery_date', 'total_value', 'currency', 'payment_terms_days',
            'batch_order_id', 'sales_rep', 'special_instructions',
            'quality_requirements', 'invoice_number', 'invoice_date', 'notes'
        ]
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'required_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'promised_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'actual_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'special_instructions': forms.Textarea(attrs={'rows': 3}),
            'quality_requirements': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class SalesOrderLineForm(forms.ModelForm):
    """Form for sales order line item."""

    class Meta:
        model = SalesOrderLine
        fields = [
            'sales_order', 'line_number', 'item_id', 'mat_number', 'description',
            'quantity_ordered', 'quantity_shipped', 'quantity_delivered', 'uom',
            'unit_price', 'discount_percent', 'line_total',
            'assigned_serial_numbers', 'notes'
        ]
        widgets = {
            'assigned_serial_numbers': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


# ============================================================================
# Drilling Operations Forms
# ============================================================================

class DrillingRunForm(forms.ModelForm):
    """Form for drilling run data entry."""

    class Meta:
        model = DrillingRun
        fields = [
            'serial_unit_id', 'bit_serial_number', 'mat_number', 'bit_size_inches',
            'run_sequence', 'customer', 'well', 'rig', 'hole_section', 'hole_type',
            'depth_in_ft', 'depth_out_ft', 'tvd_in_ft', 'tvd_out_ft',
            'footage_drilled', 'hours_on_bottom', 'avg_rop', 'max_rop',
            'avg_wob_klbs', 'max_wob_klbs', 'avg_rpm', 'max_rpm',
            'avg_flow_rate_gpm', 'avg_standpipe_psi', 'avg_torque_kftlbs',
            'mud_type', 'mud_weight_ppg',
            'nozzle_configuration', 'tfa_sqin',
            'formation_name', 'lithology',
            'run_in_date', 'run_out_date', 'status', 'trip_reason',
            'problems_encountered', 'downhole_tool_failures',
            'dull_grade_id', 'operational_summary',
            'reported_by', 'report_date', 'notes'
        ]
        widgets = {
            'run_in_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'run_out_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'report_date': forms.DateInput(attrs={'type': 'date'}),
            'lithology': forms.Textarea(attrs={'rows': 2}),
            'problems_encountered': forms.Textarea(attrs={'rows': 3}),
            'downhole_tool_failures': forms.Textarea(attrs={'rows': 2}),
            'operational_summary': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


# ============================================================================
# Dull Grade Evaluation Forms
# ============================================================================

class DullGradeEvaluationForm(forms.ModelForm):
    """Form for IADC dull grade evaluation."""

    class Meta:
        model = DullGradeEvaluation
        fields = [
            'serial_unit_id', 'bit_serial_number', 'mat_number',
            'drilling_run_id', 'run_sequence', 'customer', 'well', 'rig',
            'inner_cutting_structure', 'outer_cutting_structure',
            'primary_dull_characteristic', 'secondary_dull_characteristic',
            'dull_location', 'bearing_seal', 'gauge_condition',
            'other_dull_characteristic', 'reason_pulled',
            'cutter_wear_percent', 'gauge_wear_inches',
            'impact_damage', 'abrasion_notes', 'thermal_damage',
            'erosion_notes', 'bit_balling_observed', 'cutter_loss_count',
            'blade_damage_notes', 'evaluation_date', 'evaluation_source',
            'evaluated_by', 'evaluator_name', 'evaluation_location',
            'recommended_action', 'recommendation_notes', 'ncr_id', 'notes'
        ]
        widgets = {
            'evaluation_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'impact_damage': forms.Textarea(attrs={'rows': 2}),
            'abrasion_notes': forms.Textarea(attrs={'rows': 2}),
            'thermal_damage': forms.Textarea(attrs={'rows': 2}),
            'erosion_notes': forms.Textarea(attrs={'rows': 2}),
            'blade_damage_notes': forms.Textarea(attrs={'rows': 2}),
            'recommendation_notes': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for IADC fields
        self.fields['inner_cutting_structure'].help_text = (
            "Inner 2/3 cutting structure wear (0=No Wear, 8=100% Worn)"
        )
        self.fields['outer_cutting_structure'].help_text = (
            "Outer 1/3 cutting structure wear (0=No Wear, 8=100% Worn)"
        )
        self.fields['gauge_condition'].help_text = (
            "I=In Gauge, 1-8 = sixteenths of an inch under gauge"
        )


# ============================================================================
# Lifecycle Tracking Forms
# ============================================================================

class BitLifecycleEventForm(forms.ModelForm):
    """Form for recording bit lifecycle events."""

    class Meta:
        model = BitLifecycleEvent
        fields = [
            'serial_unit_id', 'bit_serial_number', 'mat_number',
            'event_type', 'event_datetime', 'customer', 'well', 'rig',
            'location_description', 'job_card_id', 'sales_order_id',
            'drilling_run_id', 'dull_grade_id', 'shipment_id', 'ncr_id',
            'junk_sale_id', 'description', 'notes',
            'previous_status', 'new_status',
            'previous_location', 'new_location',
            'cumulative_footage', 'cumulative_hours', 'run_count',
            'recorded_by', 'recorded_by_name'
        ]
        widgets = {
            'event_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class ShipmentForm(forms.ModelForm):
    """Form for shipment tracking."""

    class Meta:
        model = Shipment
        fields = [
            'shipment_type', 'status', 'sales_order_id',
            'from_location', 'from_customer', 'from_rig',
            'to_location', 'to_customer', 'to_rig', 'to_well',
            'carrier', 'tracking_number', 'waybill_number',
            'ship_date', 'expected_delivery_date', 'actual_delivery_date',
            'shipping_cost', 'insurance_cost',
            'bit_serial_numbers', 'contents_description',
            'total_weight_kg', 'number_of_packages',
            'packing_list_url', 'commercial_invoice_url',
            'shipper_name', 'receiver_name', 'receiver_phone',
            'handling_instructions', 'confirmed_by', 'confirmation_date', 'notes'
        ]
        widgets = {
            'ship_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'actual_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'confirmation_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'bit_serial_numbers': forms.Textarea(attrs={'rows': 2}),
            'contents_description': forms.Textarea(attrs={'rows': 3}),
            'handling_instructions': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class JunkSaleForm(forms.ModelForm):
    """Form for junk/scrap sale recording."""

    class Meta:
        model = JunkSale
        fields = [
            'serial_unit_id', 'bit_serial_number', 'mat_number',
            'gross_weight_kg', 'net_weight_kg', 'carbide_weight_kg',
            'steel_weight_kg', 'price_per_kg', 'carbide_price_per_kg',
            'buyer_name', 'buyer_contact', 'buyer_reference',
            'sale_date', 'invoice_number', 'payment_status', 'payment_date',
            'scrap_reason', 'last_dull_grade',
            'total_footage_drilled', 'total_hours_drilled', 'total_runs',
            'status', 'weight_certificate_url', 'approved_by',
            'approval_date', 'notes'
        ]
        widgets = {
            'sale_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'approval_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


# ============================================================================
# Filter/Search Forms
# ============================================================================

class BitLifecycleSearchForm(forms.Form):
    """Search form for bit lifecycle timeline."""
    bit_serial_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter bit serial number...',
            'class': 'form-control'
        })
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_deleted=False),
        required=False,
        empty_label='All Customers'
    )
    event_type = forms.ChoiceField(
        choices=[('', 'All Events')] + list(BitLifecycleEvent.EVENT_TYPE_CHOICES),
        required=False
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )


class DrillingRunSearchForm(forms.Form):
    """Search form for drilling runs."""
    bit_serial_number = forms.CharField(max_length=100, required=False)
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_deleted=False),
        required=False,
        empty_label='All Customers'
    )
    well = forms.ModelChoiceField(
        queryset=Well.objects.filter(is_deleted=False),
        required=False,
        empty_label='All Wells'
    )
    rig = forms.ModelChoiceField(
        queryset=Rig.objects.filter(is_deleted=False),
        required=False,
        empty_label='All Rigs'
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(DrillingRun.STATUS_CHOICES),
        required=False
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
