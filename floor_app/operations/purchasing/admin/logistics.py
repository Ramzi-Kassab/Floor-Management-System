"""
Logistics Admin Configuration (Transfers, Shipments, Customer Returns)
"""

from django.contrib import admin
from floor_app.operations.purchasing.models import (
    InternalTransferOrder,
    TransferOrderLine,
    OutboundShipment,
    ShipmentLine,
    CustomerReturn,
    CustomerReturnLine,
)


# ========== Internal Transfer Orders ==========
class TransferOrderLineInline(admin.TabularInline):
    model = TransferOrderLine
    extra = 1
    fields = [
        'line_number', 'item_id', 'item_code', 'description',
        'quantity_to_transfer', 'uom', 'quantity_picked',
        'quantity_received', 'is_fully_received'
    ]
    readonly_fields = ['is_fully_received']


@admin.register(InternalTransferOrder)
class InternalTransferOrderAdmin(admin.ModelAdmin):
    list_display = [
        'transfer_number', 'transfer_type', 'status', 'priority',
        'source_location_name', 'destination_location_name',
        'request_date', 'required_by_date', 'total_items'
    ]
    list_filter = ['status', 'transfer_type', 'priority', 'request_date']
    search_fields = ['transfer_number', 'source_location_name', 'destination_location_name']
    readonly_fields = [
        'public_id', 'transfer_number', 'total_items',
        'total_quantity', 'total_value',
        'picked_at', 'shipped_date', 'received_date',
        'approved_at', 'created_at', 'updated_at'
    ]
    inlines = [TransferOrderLineInline]
    date_hierarchy = 'request_date'


# ========== Outbound Shipments ==========
class ShipmentLineInline(admin.TabularInline):
    model = ShipmentLine
    extra = 1
    fields = [
        'line_number', 'item_id', 'item_code', 'description',
        'quantity_ordered', 'quantity_picked', 'quantity_shipped',
        'uom', 'unit_price', 'total_value'
    ]
    readonly_fields = ['total_value']


@admin.register(OutboundShipment)
class OutboundShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'shipment_number', 'shipment_type', 'status',
        'customer_name', 'created_date', 'scheduled_ship_date',
        'actual_ship_date', 'tracking_number', 'total_value'
    ]
    list_filter = ['status', 'shipment_type', 'created_date', 'delivery_country']
    search_fields = [
        'shipment_number', 'customer_name', 'customer_reference',
        'tracking_number', 'rig_name'
    ]
    readonly_fields = [
        'public_id', 'shipment_number', 'total_packages',
        'total_weight_kg', 'total_value',
        'actual_ship_date', 'actual_delivery_date',
        'created_at', 'updated_at'
    ]
    inlines = [ShipmentLineInline]
    date_hierarchy = 'created_date'

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'shipment_number', 'shipment_type', 'status',
                'public_id'
            )
        }),
        ('Customer Information', {
            'fields': (
                'customer_id', 'customer_name', 'customer_reference'
            )
        }),
        ('Delivery Address', {
            'fields': (
                'delivery_contact_name', 'delivery_contact_phone',
                'delivery_address_line1', 'delivery_address_line2',
                'delivery_city', 'delivery_state', 'delivery_postal_code',
                'delivery_country'
            )
        }),
        ('Rig Details (if applicable)', {
            'fields': ('rig_name', 'rig_location', 'well_name', 'field_name'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': (
                'created_date', 'scheduled_ship_date', 'actual_ship_date',
                'expected_delivery_date', 'actual_delivery_date'
            )
        }),
        ('Shipping Details', {
            'fields': (
                'carrier_name', 'shipping_method', 'tracking_number',
                'waybill_number', 'vehicle_number', 'driver_name', 'driver_phone'
            )
        }),
        ('Package Information', {
            'fields': ('total_packages', 'total_weight_kg', 'total_volume_cbm')
        }),
        ('Terms & Financials', {
            'fields': (
                'incoterm', 'currency', 'shipping_cost',
                'insurance_cost', 'total_value'
            )
        }),
        ('Export Documentation', {
            'fields': (
                'export_declaration_number', 'certificate_of_origin',
                'commercial_invoice_number', 'packing_list_number'
            ),
            'classes': ('collapse',)
        }),
        ('Delivery Confirmation', {
            'fields': (
                'delivery_confirmed', 'delivered_to',
                'delivery_notes', 'delivery_photos'
            )
        }),
        ('Notes', {
            'fields': ('special_instructions', 'notes', 'internal_notes')
        }),
    )


# ========== Customer Returns ==========
class CustomerReturnLineInline(admin.TabularInline):
    model = CustomerReturnLine
    extra = 0
    fields = [
        'line_number', 'item_id', 'item_code', 'description',
        'quantity_returned', 'uom', 'condition', 'unit_price',
        'total_value', 'line_inspection_result'
    ]
    readonly_fields = ['total_value']


@admin.register(CustomerReturn)
class CustomerReturnAdmin(admin.ModelAdmin):
    list_display = [
        'return_number', 'status', 'customer_name',
        'return_request_date', 'reason', 'rma_number',
        'inspection_result', 'resolution_type', 'total_value'
    ]
    list_filter = ['status', 'reason', 'inspection_result', 'resolution_type', 'return_request_date']
    search_fields = ['return_number', 'customer_name', 'rma_number']
    readonly_fields = [
        'public_id', 'return_number', 'total_items', 'total_value',
        'approved_at', 'received_date', 'inspection_date',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['original_shipment']
    inlines = [CustomerReturnLineInline]
    date_hierarchy = 'return_request_date'
