"""
Admin registration for core app models.
"""

from django.contrib import admin
from .models import (
    UserPreference,
    CostCenter,
    ERPDocumentType,
    ERPReference,
    LossOfSaleCause,
    LossOfSaleEvent,
    ApprovalType,
    ApprovalAuthority,
    Currency,
    ExchangeRate,
    Notification,
    ActivityLog,
)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'font_size', 'table_density', 'updated_at']
    list_filter = ['theme', 'font_size', 'table_density']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'manager', 'status', 'annual_budget', 'currency']
    list_filter = ['status', 'currency']
    search_fields = ['code', 'name', 'description', 'erp_cost_center_code']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['parent', 'manager']


@admin.register(ERPDocumentType)
class ERPDocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'erp_system', 'is_active']
    list_filter = ['is_active', 'erp_system']
    search_fields = ['code', 'name', 'description']


@admin.register(ERPReference)
class ERPReferenceAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'erp_number', 'erp_line_number', 'content_type', 'object_id', 'sync_status', 'created_at']
    list_filter = ['document_type', 'sync_status', 'content_type']
    search_fields = ['erp_number', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'last_synced']
    date_hierarchy = 'created_at'


@admin.register(LossOfSaleCause)
class LossOfSaleCauseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name', 'description']


@admin.register(LossOfSaleEvent)
class LossOfSaleEventAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'title', 'cause', 'event_date', 'estimated_loss_amount', 'currency', 'status', 'reported_by']
    list_filter = ['status', 'cause__category', 'cause', 'cost_center']
    search_fields = ['reference_number', 'title', 'description', 'affected_customer_name', 'affected_order_number']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at', 'approved_at']
    date_hierarchy = 'event_date'
    autocomplete_fields = ['cause', 'cost_center', 'reported_by', 'reviewed_by', 'approved_by']


@admin.register(ApprovalType)
class ApprovalTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'description']


@admin.register(ApprovalAuthority)
class ApprovalAuthorityAdmin(admin.ModelAdmin):
    list_display = ['approval_type', 'user', 'group', 'position_id', 'min_amount', 'max_amount', 'priority', 'is_active']
    list_filter = ['approval_type', 'is_active']
    search_fields = ['user__username', 'group__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'decimal_places', 'is_base_currency', 'is_active']
    list_filter = ['is_active', 'is_base_currency']
    search_fields = ['code', 'name']


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['from_currency', 'to_currency', 'rate', 'effective_date']
    list_filter = ['from_currency', 'to_currency']
    date_hierarchy = 'effective_date'
    readonly_fields = ['created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'priority', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['user', 'created_by']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(request, f'{queryset.count()} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_unread(self, request, queryset):
        for notification in queryset:
            notification.mark_as_unread()
        self.message_user(request, f'{queryset.count()} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'description', 'content_type', 'object_id', 'ip_address', 'created_at']
    list_filter = ['action', 'content_type', 'created_at']
    search_fields = ['user__username', 'description', 'ip_address']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['user']
    
    def has_add_permission(self, request):
        # Activity logs should not be manually created
        return False
    
    def has_change_permission(self, request, obj=None):
        # Activity logs should not be modified
        return False
