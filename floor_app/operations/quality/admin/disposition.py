"""
Quality Management - Quality Disposition Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from ..models import QualityDisposition


@admin.register(QualityDisposition)
class QualityDispositionAdmin(admin.ModelAdmin):
    list_display = [
        'job_card_id', 'decision', 'disposition_date', 'quality_engineer',
        'released_for_shipment', 'coc_number', 'customer_name'
    ]
    list_filter = [
        'decision', 'released_for_shipment', 'customer_concession',
        'customer_requirements_met'
    ]
    search_fields = [
        'coc_number', 'customer_name', 'customer_po_number',
        'inspection_summary', 'notes'
    ]
    date_hierarchy = 'disposition_date'
    raw_id_fields = ['quality_engineer', 'acceptance_template', 'released_by']
    filter_horizontal = ['ncrs_closed']
    readonly_fields = [
        'public_id', 'disposition_date', 'is_releasable_display',
        'has_open_ncrs_display', 'coc_generated_at', 'release_date',
        'created_at', 'created_by', 'updated_at', 'updated_by'
    ]

    fieldsets = (
        ('Job Reference', {
            'fields': ('job_card_id', 'evaluation_session_id')
        }),
        ('Decision', {
            'fields': (
                'decision', 'disposition_date', 'quality_engineer',
                'is_releasable_display', 'has_open_ncrs_display'
            )
        }),
        ('Inspection Summary', {
            'fields': ('inspection_summary',)
        }),
        ('Deviations & Concessions', {
            'fields': (
                'deviations_accepted', 'customer_concession', 'concession_reference'
            )
        }),
        ('Acceptance Criteria', {
            'fields': ('acceptance_template', 'criteria_results_json')
        }),
        ('NCRs', {
            'fields': ('ncrs_closed',)
        }),
        ('Certificate of Conformance', {
            'fields': ('coc_number', 'coc_generated_at')
        }),
        ('Customer Information', {
            'fields': (
                'customer_name', 'customer_po_number', 'customer_requirements_met'
            )
        }),
        ('Release Authorization', {
            'fields': (
                'released_for_shipment', 'release_date', 'released_by'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit Trail', {
            'classes': ('collapse',),
            'fields': ('public_id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'remarks')
        }),
    )

    def is_releasable_display(self, obj):
        if obj.is_releasable:
            return format_html('<span style="color: green;">✓ Releasable</span>')
        return format_html('<span style="color: red;">✗ Not Releasable</span>')

    is_releasable_display.short_description = 'Releasability'

    def has_open_ncrs_display(self, obj):
        if obj.has_open_ncrs:
            return format_html('<span style="color: red;">✗ Has Open NCRs</span>')
        return format_html('<span style="color: green;">✓ No Open NCRs</span>')

    has_open_ncrs_display.short_description = 'NCR Status'

    actions = ['generate_coc', 'authorize_release']

    def generate_coc(self, request, queryset):
        count = 0
        for disposition in queryset.filter(coc_number=''):
            disposition.generate_coc_number()
            count += 1
        self.message_user(request, f'Generated COC numbers for {count} dispositions.')

    generate_coc.short_description = 'Generate COC number'

    def authorize_release(self, request, queryset):
        count = 0
        errors = []
        for disposition in queryset:
            try:
                disposition.release(request.user)
                count += 1
            except ValueError as e:
                errors.append(f'Job #{disposition.job_card_id}: {str(e)}')

        if count:
            self.message_user(request, f'Released {count} dispositions.')
        if errors:
            self.message_user(request, f'Errors: {"; ".join(errors)}', level='WARNING')

    authorize_release.short_description = 'Authorize release for shipment'

    def save_model(self, request, obj, form, change):
        if not obj.quality_engineer_id:
            obj.quality_engineer = request.user
        super().save_model(request, obj, form, change)
