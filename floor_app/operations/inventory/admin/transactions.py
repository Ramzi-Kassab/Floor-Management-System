from django.contrib import admin
from floor_app.operations.inventory.models import InventoryTransaction


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_number', 'transaction_type', 'transaction_date',
        'item', 'serial_unit', 'quantity', 'reference_type', 'reference_id'
    ]
    list_filter = [
        'transaction_type', 'transaction_date', 'is_reversed'
    ]
    search_fields = [
        'transaction_number', 'item__sku', 'serial_unit__serial_number',
        'reference_id'
    ]
    ordering = ['-transaction_date', '-id']
    readonly_fields = [
        'transaction_number', 'posting_ts'
    ]
    raw_id_fields = [
        'item', 'serial_unit', 'uom',
        'from_location', 'to_location',
        'from_condition', 'to_condition',
        'from_ownership', 'to_ownership',
        'from_mat', 'to_mat',
        'created_by', 'reversed_by'
    ]
    date_hierarchy = 'transaction_date'

    fieldsets = (
        ('Transaction Info', {
            'fields': ('transaction_number', 'transaction_type', 'transaction_date', 'posting_ts')
        }),
        ('Items', {
            'fields': ('item', 'serial_unit', 'quantity', 'uom')
        }),
        ('Location Change', {
            'fields': ('from_location', 'to_location')
        }),
        ('Condition Change', {
            'fields': ('from_condition', 'to_condition')
        }),
        ('Ownership Change', {
            'fields': ('from_ownership', 'to_ownership')
        }),
        ('MAT Change', {
            'fields': ('from_mat', 'to_mat')
        }),
        ('Reference', {
            'fields': ('reference_type', 'reference_id', 'batch_id', 'job_card_id', 'work_order_id')
        }),
        ('Cost', {
            'fields': ('unit_cost', 'total_cost', 'currency')
        }),
        ('Status', {
            'fields': ('is_reversed', 'reversed_by')
        }),
        ('Audit', {
            'fields': ('created_by', 'reason_code', 'notes')
        }),
    )

    def has_change_permission(self, request, obj=None):
        # Transactions should be immutable
        return False

    def has_delete_permission(self, request, obj=None):
        # Transactions should never be deleted
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'item', 'serial_unit', 'uom',
            'from_location', 'to_location'
        )
