from django.contrib import admin
from floor_app.operations.inventory.models import (
    Location,
    SerialUnit,
    SerialUnitMATHistory,
    InventoryStock,
)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'location_type', 'parent_location', 'is_active']
    list_filter = ['is_active', 'location_type']
    search_fields = ['code', 'name']
    ordering = ['code']
    raw_id_fields = ['parent_location']


class SerialUnitMATHistoryInline(admin.TabularInline):
    model = SerialUnitMATHistory
    extra = 0
    readonly_fields = ['old_mat', 'new_mat', 'reason', 'changed_at', 'changed_by']
    can_delete = False


@admin.register(SerialUnit)
class SerialUnitAdmin(admin.ModelAdmin):
    list_display = [
        'serial_number', 'item', 'current_mat', 'location',
        'status', 'condition', 'ownership', 'created_at'
    ]
    list_filter = [
        'status', 'condition', 'ownership', 'is_deleted'
    ]
    search_fields = ['serial_number', 'item__sku', 'current_mat__mat_number']
    ordering = ['-created_at']
    readonly_fields = [
        'public_id', 'created_at', 'updated_at', 'created_by', 'updated_by'
    ]
    raw_id_fields = ['item', 'current_mat', 'location', 'condition', 'ownership']
    inlines = [SerialUnitMATHistoryInline]

    fieldsets = (
        ('Identification', {
            'fields': ('serial_number', 'item', 'current_mat', 'public_id')
        }),
        ('Current State', {
            'fields': ('location', 'status', 'condition', 'ownership')
        }),
        ('Lifecycle', {
            'fields': ('manufacture_date', 'received_date', 'last_run_date', 'warranty_expiry')
        }),
        ('Usage Tracking', {
            'fields': ('total_run_hours', 'total_footage_drilled', 'run_count')
        }),
        ('Cost', {
            'fields': ('acquisition_cost', 'current_book_value')
        }),
        ('Job Information', {
            'fields': ('current_customer', 'current_job_reference')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'item', 'current_mat', 'location', 'condition', 'ownership'
        )


@admin.register(InventoryStock)
class InventoryStockAdmin(admin.ModelAdmin):
    list_display = [
        'item', 'location', 'condition', 'ownership',
        'quantity_on_hand', 'quantity_reserved', 'quantity_available'
    ]
    list_filter = ['condition', 'ownership', 'location']
    search_fields = ['item__sku', 'item__name']
    ordering = ['item__sku']
    raw_id_fields = ['item', 'location', 'condition', 'ownership']
    readonly_fields = ['quantity_available', 'total_value', 'created_at', 'updated_at']

    fieldsets = (
        ('Dimensions', {
            'fields': ('item', 'location', 'condition', 'ownership')
        }),
        ('Quantities', {
            'fields': ('quantity_on_hand', 'quantity_reserved', 'quantity_available', 'quantity_on_order')
        }),
        ('Reorder Settings', {
            'fields': ('reorder_point', 'safety_stock')
        }),
        ('Cost', {
            'fields': ('unit_cost', 'total_value')
        }),
        ('Audit', {
            'fields': ('last_counted_at', 'last_movement_at', 'created_at', 'updated_at', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def quantity_available(self, obj):
        return obj.quantity_available
    quantity_available.short_description = 'Available'

    def total_value(self, obj):
        return obj.total_value
    total_value.short_description = 'Total Value'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'item', 'location', 'condition', 'ownership'
        )
