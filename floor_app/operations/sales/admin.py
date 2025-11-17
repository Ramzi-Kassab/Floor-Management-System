"""
Sales, Lifecycle & Drilling Operations - Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Customer, Rig, Well,
    SalesOpportunity, SalesOrder, SalesOrderLine,
    DrillingRun,
    DullGradeEvaluation,
    BitLifecycleEvent, Shipment, JunkSale,
)


# ============================================================================
# Inlines
# ============================================================================

class SalesOrderLineInline(admin.TabularInline):
    model = SalesOrderLine
    extra = 0
    fields = [
        'line_number', 'mat_number', 'description',
        'quantity_ordered', 'quantity_shipped', 'unit_price', 'line_total'
    ]
    readonly_fields = ['line_total']


# ============================================================================
# Customer Management Admin
# ============================================================================

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'customer_code', 'name', 'customer_type', 'account_status',
        'is_billing_entity', 'is_operating_entity', 'region', 'country'
    ]
    list_filter = [
        'customer_type', 'account_status', 'region', 'country',
        'is_billing_entity', 'is_operating_entity',
        'requires_coc', 'requires_dull_grade'
    ]
    search_fields = [
        'customer_code', 'name', 'legal_name', 'tax_id',
        'primary_contact_email'
    ]
    readonly_fields = ['public_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('customer_code', 'name', 'legal_name', 'tax_id', 'public_id')
        }),
        ('Classification', {
            'fields': (
                'customer_type', 'account_status', 'parent_company',
                'is_billing_entity', 'is_operating_entity', 'billing_customer'
            )
        }),
        ('Contact Information', {
            'fields': (
                'primary_contact_name', 'primary_contact_email',
                'primary_contact_phone', 'billing_address', 'shipping_address'
            )
        }),
        ('Location', {
            'fields': ('region', 'country', 'state_province', 'city')
        }),
        ('Financial', {
            'fields': ('payment_terms_days', 'credit_limit', 'currency')
        }),
        ('Requirements', {
            'fields': (
                'requires_coc', 'requires_dull_grade',
                'custom_report_format', 'special_requirements'
            )
        }),
        ('Sales', {
            'fields': ('assigned_sales_rep', 'contract_expiry_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Rig)
class RigAdmin(admin.ModelAdmin):
    list_display = [
        'rig_code', 'name', 'rig_type', 'status',
        'owner_customer', 'current_location', 'year_built'
    ]
    list_filter = ['rig_type', 'status', 'year_built', 'top_drive']
    search_fields = ['rig_code', 'name', 'current_location']
    readonly_fields = ['public_id', 'created_at', 'updated_at']
    autocomplete_fields = ['owner_customer', 'operator_customer', 'drilling_contractor']


@admin.register(Well)
class WellAdmin(admin.ModelAdmin):
    list_display = [
        'well_name', 'well_type', 'status', 'operator_customer',
        'field_name', 'current_rig', 'spud_date'
    ]
    list_filter = ['well_type', 'status', 'field_name']
    search_fields = ['well_name', 'uwi', 'api_number', 'field_name']
    readonly_fields = ['public_id', 'created_at', 'updated_at']
    autocomplete_fields = ['operator_customer', 'current_rig']


# ============================================================================
# Sales Management Admin
# ============================================================================

@admin.register(SalesOpportunity)
class SalesOpportunityAdmin(admin.ModelAdmin):
    list_display = [
        'opportunity_number', 'name', 'customer', 'status',
        'probability_display', 'estimated_value', 'weighted_value_display',
        'expected_delivery_date'
    ]
    list_filter = ['status', 'probability', 'expected_delivery_date']
    search_fields = ['opportunity_number', 'name', 'customer__name', 'mat_number']
    readonly_fields = ['public_id', 'opportunity_number', 'weighted_value_display', 'created_at', 'updated_at']
    autocomplete_fields = ['customer', 'well', 'rig', 'sales_rep']
    date_hierarchy = 'expected_delivery_date'

    def probability_display(self, obj):
        color = 'green' if obj.probability >= 75 else 'orange' if obj.probability >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            f"{obj.probability}%"
        )
    probability_display.short_description = 'Probability'

    def weighted_value_display(self, obj):
        return f"${obj.weighted_value:,.2f}"
    weighted_value_display.short_description = 'Weighted Value'


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer', 'status', 'priority',
        'order_date', 'required_delivery_date', 'total_value_display',
        'is_overdue_display'
    ]
    list_filter = ['status', 'priority', 'order_date', 'required_delivery_date']
    search_fields = [
        'order_number', 'customer_po_number', 'customer__name',
        'customer__customer_code'
    ]
    readonly_fields = [
        'public_id', 'order_number', 'total_value',
        'is_overdue_display', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['customer', 'billing_customer', 'well', 'rig', 'sales_rep']
    inlines = [SalesOrderLineInline]
    date_hierarchy = 'order_date'

    fieldsets = (
        ('Order Information', {
            'fields': (
                'order_number', 'customer_po_number', 'status', 'priority',
                'public_id'
            )
        }),
        ('Customer', {
            'fields': ('customer', 'billing_customer', 'well', 'rig')
        }),
        ('Dates', {
            'fields': (
                'order_date', 'required_delivery_date',
                'promised_delivery_date', 'actual_ship_date'
            )
        }),
        ('Financial', {
            'fields': ('total_value', 'discount_percent', 'tax_amount')
        }),
        ('Production Link', {
            'fields': ('batch_order_id',)
        }),
        ('Sales', {
            'fields': ('sales_rep', 'commission_percent')
        }),
        ('Shipping', {
            'fields': ('shipping_method', 'shipping_instructions')
        }),
        ('Notes', {
            'fields': ('internal_notes', 'customer_notes')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_value_display(self, obj):
        return f"${obj.total_value:,.2f}"
    total_value_display.short_description = 'Total Value'

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">OVERDUE</span>')
        return format_html('<span style="color: green;">On Time</span>')
    is_overdue_display.short_description = 'Delivery Status'


@admin.register(SalesOrderLine)
class SalesOrderLineAdmin(admin.ModelAdmin):
    list_display = [
        'sales_order', 'line_number', 'mat_number', 'description',
        'quantity_ordered', 'quantity_shipped', 'unit_price', 'line_total'
    ]
    list_filter = ['sales_order__status']
    search_fields = ['sales_order__order_number', 'mat_number', 'description']
    readonly_fields = ['public_id', 'created_at', 'updated_at']


# ============================================================================
# Drilling Operations Admin
# ============================================================================

@admin.register(DrillingRun)
class DrillingRunAdmin(admin.ModelAdmin):
    list_display = [
        'run_number', 'bit_serial_number', 'well', 'rig',
        'hole_section', 'footage_drilled', 'avg_rop',
        'status', 'run_in_date'
    ]
    list_filter = ['status', 'mud_type', 'run_in_date']
    search_fields = [
        'run_number', 'bit_serial_number', 'mat_number',
        'well__well_name', 'rig__name'
    ]
    readonly_fields = [
        'public_id', 'run_number', 'footage_drilled', 'avg_rop',
        'created_at', 'updated_at'
    ]
    autocomplete_fields = ['customer', 'well', 'rig']
    date_hierarchy = 'run_in_date'

    fieldsets = (
        ('Identification', {
            'fields': (
                'run_number', 'serial_unit_id', 'bit_serial_number',
                'mat_number', 'run_sequence', 'public_id'
            )
        }),
        ('Location', {
            'fields': ('customer', 'well', 'rig', 'hole_section')
        }),
        ('Depth & Performance', {
            'fields': (
                'depth_in_ft', 'depth_out_ft', 'footage_drilled',
                'hours_on_bottom', 'avg_rop', 'max_rop', 'min_rop'
            )
        }),
        ('Operating Parameters', {
            'fields': (
                'avg_wob_klbs', 'max_wob_klbs', 'avg_rpm', 'max_rpm',
                'avg_flow_rate_gpm', 'avg_standpipe_psi', 'avg_torque_kftlbs',
                'max_torque_kftlbs'
            )
        }),
        ('Mud Properties', {
            'fields': (
                'mud_type', 'mud_weight_ppg', 'plastic_viscosity',
                'yield_point', 'mud_properties_json'
            )
        }),
        ('Nozzles', {
            'fields': ('nozzle_configuration', 'tfa_sqin', 'hsi')
        }),
        ('Formation', {
            'fields': (
                'formation_name', 'lithology', 'formation_hardness',
                'abrasiveness_estimate'
            )
        }),
        ('Problems & Trip', {
            'fields': ('problems_encountered', 'trip_reason', 'vibration_notes')
        }),
        ('Status & Timing', {
            'fields': ('status', 'run_in_date', 'run_out_date')
        }),
        ('Additional Data', {
            'fields': (
                'bha_details_json', 'directional_data_json',
                'motor_details', 'mwd_lwd_data_json'
            ),
            'classes': ('collapse',)
        }),
        ('Links', {
            'fields': ('dull_grade_id', 'job_card_id', 'data_source')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# Dull Grade Admin
# ============================================================================

@admin.register(DullGradeEvaluation)
class DullGradeEvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'evaluation_number', 'bit_serial_number', 'iadc_dull_grade',
        'customer', 'severity_score_display', 'is_rerunnable_display',
        'evaluation_date', 'evaluation_source'
    ]
    list_filter = [
        'evaluation_source', 'primary_dull_characteristic',
        'gauge_condition', 'reason_pulled', 'evaluation_date'
    ]
    search_fields = [
        'evaluation_number', 'bit_serial_number', 'mat_number',
        'customer__name', 'well__well_name'
    ]
    readonly_fields = [
        'public_id', 'evaluation_number', 'iadc_dull_grade',
        'severity_score_display', 'is_rerunnable_display',
        'created_at', 'updated_at'
    ]
    autocomplete_fields = ['customer', 'well', 'rig', 'evaluated_by']
    date_hierarchy = 'evaluation_date'

    fieldsets = (
        ('Identification', {
            'fields': (
                'evaluation_number', 'serial_unit_id', 'bit_serial_number',
                'mat_number', 'drilling_run_id', 'run_sequence', 'public_id'
            )
        }),
        ('Context', {
            'fields': ('customer', 'well', 'rig')
        }),
        ('IADC Dull Grade', {
            'fields': (
                'inner_cutting_structure', 'outer_cutting_structure',
                'primary_dull_characteristic', 'secondary_dull_characteristic',
                'dull_location', 'bearing_seal', 'gauge_condition',
                'other_dull_characteristic', 'reason_pulled', 'iadc_dull_grade'
            )
        }),
        ('Measurements', {
            'fields': ('cutter_wear_percent', 'gauge_wear_inches')
        }),
        ('Detailed Observations', {
            'fields': (
                'impact_damage', 'abrasion_notes', 'thermal_damage',
                'erosion_notes', 'bit_balling_observed', 'cutter_loss_count',
                'blade_damage_notes'
            )
        }),
        ('Photos', {
            'fields': ('photos_json',)
        }),
        ('Evaluation Details', {
            'fields': (
                'evaluation_date', 'evaluation_source', 'evaluated_by',
                'evaluator_name', 'evaluation_location'
            )
        }),
        ('Recommendations', {
            'fields': (
                'recommended_action', 'recommendation_notes',
                'severity_score_display', 'is_rerunnable_display'
            )
        }),
        ('Quality Link', {
            'fields': ('ncr_id',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def severity_score_display(self, obj):
        score = obj.severity_score
        if score >= 75:
            color = 'red'
        elif score >= 50:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}/100</span>',
            color, score
        )
    severity_score_display.short_description = 'Severity Score'

    def is_rerunnable_display(self, obj):
        if obj.is_rerunnable:
            return format_html('<span style="color: green;">✓ Rerunnable</span>')
        return format_html('<span style="color: red;">✗ Not Rerunnable</span>')
    is_rerunnable_display.short_description = 'Rerun Status'


# ============================================================================
# Lifecycle Tracking Admin
# ============================================================================

@admin.register(BitLifecycleEvent)
class BitLifecycleEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_number', 'bit_serial_number', 'event_type',
        'event_category', 'event_datetime', 'location_description',
        'recorded_by'
    ]
    list_filter = [
        'event_type', 'event_datetime', 'customer'
    ]
    search_fields = [
        'event_number', 'bit_serial_number', 'description',
        'location_description'
    ]
    readonly_fields = [
        'public_id', 'event_number', 'event_category',
        'created_at', 'updated_at'
    ]
    autocomplete_fields = ['customer', 'well', 'rig', 'recorded_by']
    date_hierarchy = 'event_datetime'

    fieldsets = (
        ('Identification', {
            'fields': (
                'event_number', 'serial_unit_id', 'bit_serial_number',
                'mat_number', 'public_id'
            )
        }),
        ('Event Details', {
            'fields': (
                'event_type', 'event_category', 'event_datetime',
                'description', 'notes'
            )
        }),
        ('Location', {
            'fields': ('customer', 'well', 'rig', 'location_description')
        }),
        ('State Changes', {
            'fields': (
                'previous_status', 'new_status',
                'previous_location', 'new_location'
            )
        }),
        ('Metrics', {
            'fields': ('cumulative_footage', 'cumulative_hours', 'run_count')
        }),
        ('Related Records', {
            'fields': (
                'job_card_id', 'sales_order_id', 'drilling_run_id',
                'dull_grade_id', 'shipment_id', 'ncr_id', 'junk_sale_id'
            )
        }),
        ('Recorded By', {
            'fields': ('recorded_by', 'recorded_by_name')
        }),
        ('Attachments', {
            'fields': ('attachments_json',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'shipment_number', 'shipment_type', 'status',
        'from_location', 'to_location', 'ship_date',
        'tracking_number', 'is_overdue_display'
    ]
    list_filter = ['shipment_type', 'status', 'carrier', 'ship_date']
    search_fields = [
        'shipment_number', 'tracking_number', 'waybill_number',
        'bit_serial_numbers', 'to_location'
    ]
    readonly_fields = [
        'public_id', 'shipment_number', 'is_overdue_display',
        'created_at', 'updated_at'
    ]
    autocomplete_fields = [
        'from_customer', 'from_rig', 'to_customer', 'to_rig',
        'to_well', 'confirmed_by'
    ]
    date_hierarchy = 'ship_date'

    fieldsets = (
        ('Identification', {
            'fields': (
                'shipment_number', 'sales_order_id', 'shipment_type',
                'status', 'public_id'
            )
        }),
        ('Origin', {
            'fields': ('from_location', 'from_customer', 'from_rig')
        }),
        ('Destination', {
            'fields': ('to_location', 'to_customer', 'to_rig', 'to_well')
        }),
        ('Shipping Details', {
            'fields': (
                'carrier', 'tracking_number', 'waybill_number',
                'ship_date', 'expected_delivery_date', 'actual_delivery_date',
                'is_overdue_display'
            )
        }),
        ('Costs', {
            'fields': ('shipping_cost', 'insurance_cost')
        }),
        ('Contents', {
            'fields': (
                'bit_serial_numbers', 'contents_description',
                'total_weight_kg', 'number_of_packages'
            )
        }),
        ('Documentation', {
            'fields': (
                'packing_list_url', 'commercial_invoice_url',
                'customs_documents_json'
            )
        }),
        ('Contacts', {
            'fields': ('shipper_name', 'receiver_name', 'receiver_phone')
        }),
        ('Instructions', {
            'fields': ('handling_instructions', 'notes')
        }),
        ('Confirmation', {
            'fields': ('confirmed_by', 'confirmation_date')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">OVERDUE</span>')
        return format_html('<span style="color: green;">On Time</span>')
    is_overdue_display.short_description = 'Delivery Status'


@admin.register(JunkSale)
class JunkSaleAdmin(admin.ModelAdmin):
    list_display = [
        'junk_sale_number', 'bit_serial_number', 'net_weight_kg',
        'total_sale_value_display', 'buyer_name', 'sale_date',
        'status', 'payment_status'
    ]
    list_filter = ['status', 'payment_status', 'sale_date']
    search_fields = [
        'junk_sale_number', 'bit_serial_number', 'buyer_name',
        'invoice_number'
    ]
    readonly_fields = [
        'public_id', 'junk_sale_number', 'total_sale_value',
        'recovery_rate_display', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['approved_by']
    date_hierarchy = 'sale_date'

    fieldsets = (
        ('Identification', {
            'fields': (
                'junk_sale_number', 'serial_unit_id', 'bit_serial_number',
                'mat_number', 'status', 'public_id'
            )
        }),
        ('Weight', {
            'fields': (
                'gross_weight_kg', 'net_weight_kg', 'carbide_weight_kg',
                'steel_weight_kg', 'recovery_rate_display'
            )
        }),
        ('Pricing', {
            'fields': (
                'price_per_kg', 'carbide_price_per_kg', 'total_sale_value'
            )
        }),
        ('Buyer', {
            'fields': ('buyer_name', 'buyer_contact', 'buyer_reference')
        }),
        ('Transaction', {
            'fields': (
                'sale_date', 'invoice_number', 'payment_status', 'payment_date'
            )
        }),
        ('Scrap Reason', {
            'fields': ('scrap_reason', 'last_dull_grade')
        }),
        ('Lifetime Metrics', {
            'fields': ('total_footage_drilled', 'total_hours_drilled', 'total_runs')
        }),
        ('Documentation', {
            'fields': ('weight_certificate_url', 'photos_json')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approval_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_sale_value_display(self, obj):
        return f"${obj.total_sale_value:,.2f}"
    total_sale_value_display.short_description = 'Total Value'

    def recovery_rate_display(self, obj):
        return f"{obj.recovery_rate:.1f}%"
    recovery_rate_display.short_description = 'Recovery Rate'
