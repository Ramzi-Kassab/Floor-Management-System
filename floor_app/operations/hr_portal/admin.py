"""
HR Portal Admin Configuration

Admin interface for employee portal functionality.
"""
from django.contrib import admin
from .models import EmployeeRequest


@admin.register(EmployeeRequest)
class EmployeeRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_number', 'employee', 'request_type', 'subject',
        'priority', 'status', 'submitted_date'
    ]
    list_filter = ['request_type', 'status', 'priority', 'submitted_date']
    search_fields = [
        'request_number', 'employee__employee_code',
        'employee__person__first_name', 'employee__person__last_name',
        'subject', 'description'
    ]
    readonly_fields = ['request_number', 'submitted_date', 'updated_at']
    date_hierarchy = 'submitted_date'

    fieldsets = (
        ('Request Information', {
            'fields': ('request_number', 'employee', 'request_type', 'subject', 'description')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Attachments', {
            'fields': ('attachment',)
        }),
        ('Response', {
            'fields': ('response', 'response_attachment', 'reviewed_by', 'reviewed_date', 'completed_date'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('submitted_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
