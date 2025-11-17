"""
Quality Management - Reference Tables Admin
"""
from django.contrib import admin
from ..models import DefectCategory, RootCauseCategory, AcceptanceCriteriaTemplate


@admin.register(DefectCategory)
class DefectCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'is_critical', 'sort_order', 'created_at'
    ]
    list_filter = ['is_critical']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'code']
    readonly_fields = ['public_id', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        ('Defect Category', {
            'fields': ('code', 'name', 'description', 'is_critical', 'sort_order')
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )


@admin.register(RootCauseCategory)
class RootCauseCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'sort_order', 'created_at']
    search_fields = ['code', 'name', 'description']
    ordering = ['sort_order', 'code']
    readonly_fields = ['public_id', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        ('Root Cause Category', {
            'fields': ('code', 'name', 'description', 'sort_order')
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )


@admin.register(AcceptanceCriteriaTemplate)
class AcceptanceCriteriaTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'applies_to_bit_type', 'applies_to_customer',
        'is_active', 'version', 'created_at'
    ]
    list_filter = [
        'is_active', 'applies_to_bit_type', 'applies_to_customer', 'applies_to_process'
    ]
    search_fields = ['code', 'name', 'description', 'api_standard', 'customer_spec']
    ordering = ['code']
    readonly_fields = ['public_id', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        ('Template Identification', {
            'fields': ('code', 'name', 'description', 'version', 'is_active')
        }),
        ('Applicability', {
            'fields': ('applies_to_bit_type', 'applies_to_customer', 'applies_to_process')
        }),
        ('Criteria Specification', {
            'fields': ('criteria_json',)
        }),
        ('Standard References', {
            'fields': ('api_standard', 'customer_spec', 'internal_spec')
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )
