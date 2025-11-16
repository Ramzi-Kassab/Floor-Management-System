from django.contrib import admin
from floor_app.operations.inventory.models import (
    ConditionType,
    OwnershipType,
    UnitOfMeasure,
    ItemCategory,
)


@admin.register(ConditionType)
class ConditionTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    ordering = ['sort_order', 'code']


@admin.register(OwnershipType)
class OwnershipTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_internal', 'is_consignment', 'sort_order', 'is_active']
    list_filter = ['is_active', 'is_internal', 'is_consignment']
    search_fields = ['code', 'name']
    ordering = ['sort_order', 'code']


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'uom_type', 'is_active']
    list_filter = ['is_active', 'uom_type']
    search_fields = ['code', 'name']
    ordering = ['uom_type', 'code']


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent_category', 'is_serialized', 'is_bit_related', 'is_active']
    list_filter = ['is_active', 'is_serialized', 'is_bit_related']
    search_fields = ['code', 'name']
    ordering = ['sort_order', 'code']
    raw_id_fields = ['parent_category']
