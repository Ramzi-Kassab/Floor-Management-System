from django.contrib import admin
from floor_app.operations.inventory.models import Item, ItemAttributeValue


class ItemAttributeValueInline(admin.TabularInline):
    model = ItemAttributeValue
    extra = 0
    fields = ['attribute', 'value_text', 'value_number', 'value_boolean', 'value_date']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        'sku', 'short_name', 'category', 'uom',
        'is_active', 'is_serialized', 'mat_number', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_purchasable', 'is_producible', 'is_sellable',
        'category', 'is_deleted'
    ]
    search_fields = ['sku', 'name', 'short_name', 'barcode', 'manufacturer_part_number']
    ordering = ['sku']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    raw_id_fields = ['category', 'uom', 'bit_design_revision']
    inlines = [ItemAttributeValueInline]

    fieldsets = (
        ('Identification', {
            'fields': ('sku', 'name', 'short_name', 'public_id', 'barcode')
        }),
        ('Classification', {
            'fields': ('category', 'uom', 'bit_design_revision')
        }),
        ('Inventory Planning', {
            'fields': ('min_stock_qty', 'reorder_point', 'reorder_qty', 'safety_stock', 'lead_time_days')
        }),
        ('Cost', {
            'fields': ('standard_cost', 'last_purchase_cost', 'currency')
        }),
        ('Status', {
            'fields': ('is_active', 'is_purchasable', 'is_producible', 'is_sellable', 'is_stockable')
        }),
        ('Supplier', {
            'fields': ('primary_supplier', 'manufacturer_name', 'manufacturer_part_number')
        }),
        ('Physical Properties', {
            'fields': ('weight_kg', 'volume_cbm')
        }),
        ('Documentation', {
            'fields': ('description', 'notes', 'alternative_codes')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )

    def is_serialized(self, obj):
        return obj.is_serialized
    is_serialized.boolean = True
    is_serialized.short_description = 'Serialized'

    def mat_number(self, obj):
        return obj.mat_number
    mat_number.short_description = 'MAT #'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'uom', 'bit_design_revision'
        )
