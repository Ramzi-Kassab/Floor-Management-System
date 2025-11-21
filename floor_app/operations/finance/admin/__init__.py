"""
Finance Admin Registration
"""
from django.contrib import admin
from floor_app.operations.finance.models import NCRFinancialImpact

@admin.register(NCRFinancialImpact)
class NCRFinancialImpactAdmin(admin.ModelAdmin):
    """Admin for NCR Financial Impact tracking."""
    list_display = [
        'ncr_number', 'estimated_cost_impact', 'actual_cost_impact',
        'lost_revenue', 'total_financial_impact', 'created_at'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['ncr_number', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'total_financial_impact']

    fieldsets = (
        ('NCR Reference', {
            'fields': ('ncr_number',)
        }),
        ('Cost Impact', {
            'fields': (
                'estimated_cost_impact',
                'actual_cost_impact',
                'lost_revenue',
                'total_financial_impact',
            )
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by on save."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
