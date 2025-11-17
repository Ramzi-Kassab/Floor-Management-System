"""
Supplier Admin Configuration
"""

from django.contrib import admin
from floor_app.operations.purchasing.models import (
    Supplier,
    SupplierItem,
    SupplierContact,
)


class SupplierContactInline(admin.TabularInline):
    model = SupplierContact
    extra = 1
    fields = ['name', 'title', 'email', 'phone', 'mobile', 'is_primary', 'is_active']


class SupplierItemInline(admin.TabularInline):
    model = SupplierItem
    extra = 0
    fields = [
        'item_id', 'supplier_part_number', 'unit_price',
        'currency', 'lead_time_days', 'minimum_order_quantity', 'is_preferred'
    ]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'classification', 'status',
        'default_currency', 'payment_terms', 'quality_rating',
        'total_orders', 'on_time_delivery_percentage'
    ]
    list_filter = ['status', 'classification', 'default_currency', 'iso_certified', 'api_certified']
    search_fields = ['code', 'name', 'legal_name', 'primary_email']
    readonly_fields = [
        'public_id', 'created_at', 'created_by', 'updated_at', 'updated_by',
        'total_orders', 'total_value_purchased', 'on_time_delivery_percentage',
        'quality_rating', 'last_order_date'
    ]
    inlines = [SupplierContactInline, SupplierItemInline]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'code', 'name', 'legal_name', 'classification', 'status',
                'public_id'
            )
        }),
        ('Contact Information', {
            'fields': (
                'primary_email', 'secondary_email', 'phone', 'fax', 'website'
            )
        }),
        ('Address', {
            'fields': (
                'address_line1', 'address_line2', 'city',
                'state_province', 'postal_code', 'country'
            )
        }),
        ('Commercial Terms', {
            'fields': (
                'default_currency', 'payment_terms', 'default_incoterm',
                'credit_limit', 'discount_percentage'
            )
        }),
        ('Tax & Registration', {
            'fields': (
                'tax_id', 'cr_number', 'gosi_number', 'saudization_percentage'
            )
        }),
        ('Banking Information', {
            'fields': (
                'bank_name', 'bank_branch', 'bank_account_number',
                'bank_iban', 'bank_swift_code'
            ),
            'classes': ('collapse',)
        }),
        ('Certifications', {
            'fields': (
                'iso_certified', 'iso_certificate_number', 'iso_expiry_date',
                'api_certified', 'api_certificate_number', 'api_expiry_date',
                'other_certifications'
            ),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': (
                'average_lead_time_days', 'on_time_delivery_percentage',
                'quality_rating', 'total_orders', 'total_value_purchased',
                'last_order_date'
            )
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes')
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 'remarks'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SupplierItem)
class SupplierItemAdmin(admin.ModelAdmin):
    list_display = [
        'supplier', 'item_id', 'supplier_part_number', 'unit_price',
        'currency', 'lead_time_days', 'minimum_order_quantity', 'is_preferred'
    ]
    list_filter = ['supplier', 'currency', 'is_preferred', 'requires_inspection']
    search_fields = ['supplier__code', 'supplier_part_number', 'supplier_description']
    raw_id_fields = ['supplier']
    readonly_fields = ['created_at', 'created_by', 'updated_at', 'updated_by']
