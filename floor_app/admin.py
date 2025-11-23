from django.contrib import admin

from .operations.hr.models import (
    HRPeople,
    HRPhone,
    HREmail,
    HREmployee,
    HRQualification,
    HREmployeeQualification,
    Position,
    Department,
    Address,
)
from django.utils.html import format_html
from django.urls import reverse

class HRPhoneInline(admin.TabularInline):
    model = HRPhone
    extra = 0
    autocomplete_fields = ("person",)


class HREmailInline(admin.TabularInline):
    model = HREmail
    extra = 0
    autocomplete_fields = ("person",)


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ("address_line1", "city", "hr_kind", "hr_use", "is_primary_hint")

@admin.register(HRPeople)
class HRPeopleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_full_name_en",
        "gender",
        "primary_nationality_iso2",
        "national_id",
        "iqama_number",
    )
    list_filter = (
        "gender",
        "primary_nationality_iso2",
    )
    search_fields = (
        "first_name_en",
        "last_name_en",
        "first_name_ar",
        "last_name_ar",
        "national_id",
        "iqama_number",
    )
    readonly_fields = (
        "public_id",
        "name_dob_hash",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    inlines = [HRPhoneInline, HREmailInline, AddressInline]

    fieldsets = (
        ("Names (English)", {
            "fields": ("first_name_en", "middle_name_en", "last_name_en"),
        }),
        ("Names (Arabic)", {
            "fields": ("first_name_ar", "middle_name_ar", "last_name_ar"),
            "classes": ("collapse",),
        }),
        ("Personal Information", {
            "fields": ("gender", "date_of_birth", "date_of_birth_hijri", "marital_status"),
        }),
        ("Nationality & Identification", {
            "fields": ("primary_nationality_iso2", "national_id", "iqama_number", "iqama_expiry"),
        }),
        ("Identity Verification", {
            "fields": ("identity_verified", "identity_verified_at", "identity_verified_by"),
            "classes": ("collapse",),
        }),
        ("Photo", {
            "fields": ("photo",),
        }),
        ("System Information", {
            "fields": ("public_id", "name_dob_hash", "created_at", "created_by", "updated_at", "updated_by"),
            "classes": ("collapse",),
        }),
    )


@admin.register(HRPhone)
class HRPhoneAdmin(admin.ModelAdmin):
    list_display = ("phone_e164", "country_iso2", "kind", "use", "person")
    list_filter = ("kind", "use", "country_iso2")
    search_fields = ("phone_e164",)
    autocomplete_fields = ("person",)


@admin.register(HREmail)
class HREmailAdmin(admin.ModelAdmin):
    list_display = ("email", "kind", "is_verified", "person")
    list_filter = ("kind", "is_verified")
    search_fields = ("email",)
    autocomplete_fields = ("person",)


@admin.register(HREmployee)
class HREmployeeAdmin(admin.ModelAdmin):
    change_form_template = "admin/floor_app/hremployee/change_form.html"
    change_list_template = "admin/floor_app/hremployee/change_list.html"
    list_display = ("employee_no", "person", "position", "department", "status", "contract_type")
    list_filter = ("status", "contract_type", "department", "employment_status")
    search_fields = (
        "employee_no",
        "person__first_name_en",
        "person__last_name_en",
        "person__first_name_ar",
        "person__last_name_ar",
    )

    autocomplete_fields = ("person", "user", "position", "department", "supervisor")
    readonly_fields = ("public_id", "created_at", "updated_at", "created_by", "updated_by")

    fieldsets = (
        ("Person & User", {
            "fields": ("person", "user"),
        }),
        ("Employee Details", {
            "fields": ("employee_no", "status", "employment_status"),
        }),
        ("Job Assignment", {
            "fields": ("position", "department"),
        }),
        ("Contract Information", {
            "fields": ("contract_type", "contract_start_date", "contract_end_date", "contract_renewal_date"),
        }),
        ("Probation", {
            "fields": ("probation_end_date", "probation_status"),
        }),
        ("Employment Dates", {
            "fields": ("hire_date", "termination_date"),
        }),
        ("Work Schedule", {
            "fields": ("work_days_per_week", "hours_per_week", "shift_pattern"),
        }),
        ("Compensation", {
            "fields": ("salary_grade", "monthly_salary", "benefits_eligible", "overtime_eligible"),
        }),
        ("Leave Entitlements", {
            "fields": ("annual_leave_days", "sick_leave_days", "special_leave_days"),
        }),
        ("Employment Details", {
            "fields": ("employment_category", "supervisor", "cost_center"),
        }),
        ("System Information", {
            "fields": ("public_id", "created_at", "created_by", "updated_at", "updated_by"),
            "classes": ("collapse",),
        }),
    )


@admin.register(HRQualification)
class HRQualificationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "issuer_type", "level", "validity_months", "is_active")
    list_filter = ("issuer_type", "is_active")
    search_fields = ("code", "name")


@admin.register(HREmployeeQualification)
class HREmployeeQualificationAdmin(admin.ModelAdmin):
    list_display = ("employee", "qualification", "status", "issued_at", "expires_at")
    list_filter = ("status", "qualification")
    search_fields = (
        "employee__employee_no",
        "employee__person__first_name",
        "employee__person__last_name",
        "qualification__code",
    )
    autocomplete_fields = ("employee", "qualification")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "department_type", "created_at")
    list_filter = ("department_type",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Department Information", {
            "fields": ("name", "description", "department_type"),
        }),
        ("System Information", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "position_level", "salary_grade", "is_active")
    list_filter = ("department", "position_level", "salary_grade", "is_active")
    search_fields = ("name", "description")
    autocomplete_fields = ("department",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "description", "department"),
        }),
        ("Position Details", {
            "fields": ("position_level", "salary_grade", "is_active"),
        }),
        ("System Information", {
            "fields": ("created_at", "created_by", "updated_at", "updated_by"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("address_line1", "city", "country_iso2", "verification_status")
    list_filter = ("country_iso2", "verification_status", "address_kind")
    search_fields = ("address_line1", "address_line2", "city", "postal_code")
    readonly_fields = ("public_id", "created_at", "updated_at", "created_by", "updated_by")

    fieldsets = (
        ("Address Lines", {
            "fields": ("address_line1", "address_line2"),
        }),
        ("Location Details", {
            "fields": ("city", "state_region", "postal_code", "country_iso2"),
        }),
        ("Address Type", {
            "fields": ("address_kind", "po_box", "street_name", "building_number", "unit_number", "neighborhood", "additional_number"),
        }),
        ("Geolocation", {
            "fields": ("latitude", "longitude"),
            "classes": ("collapse",),
        }),
        ("Verification", {
            "fields": ("verification_status", "label", "accessibility_notes"),
        }),
        ("HR Person Address", {
            "fields": ("hr_person", "hr_kind", "hr_use", "is_primary_hint"),
            "classes": ("collapse",),
        }),
        ("Additional", {
            "fields": ("components",),
            "classes": ("collapse",),
        }),
        ("System Information", {
            "fields": ("public_id", "created_at", "created_by", "updated_at", "updated_by"),
            "classes": ("collapse",),
        }),
    )

"""
Django Admin configurations for Floor App system models.

Provides admin interfaces for:
- Audit Logs
- API Keys
- Webhooks
- Support Tickets
- Help Articles
- Dashboard Widgets

Note: Notification admin is in floor_app.operations.notifications.admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models_system import (
    AuditLog,
    APIKey,
    Webhook,
    WebhookLog,
    SupportTicket,
    SupportTicketReply,
    HelpCategory,
    HelpArticle,
    DashboardWidget,
    DashboardLayout,
)


# ========== AUDIT LOGS ==========

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'action', 'module', 'object_type', 'ip_address']
    list_filter = ['action', 'module', 'created_at']
    search_fields = ['user__username', 'description', 'object_type', 'ip_address']
    readonly_fields = ['created_at', 'user', 'action', 'module', 'object_type',
                       'description', 'ip_address', 'user_agent', 'changes']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False  # Audit logs are created automatically

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser


# ========== API MANAGEMENT ==========

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'prefix_display', 'user', 'permission_level', 'is_active',
                    'usage_count', 'created_at']
    list_filter = ['permission_level', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['key', 'prefix', 'usage_count', 'last_used', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'user')
        }),
        ('API Key', {
            'fields': ('key', 'prefix'),
            'description': 'The API key is generated automatically. Store it securely.'
        }),
        ('Permissions & Limits', {
            'fields': ('permission_level', 'rate_limit', 'is_active', 'expires_at')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used', 'created_at')
        }),
    )

    def prefix_display(self, obj):
        return f"{obj.prefix}..."
    prefix_display.short_description = 'Key Prefix'

    actions = ['regenerate_keys', 'deactivate_keys']

    def regenerate_keys(self, request, queryset):
        count = 0
        for api_key in queryset:
            api_key.regenerate_key()
            count += 1
        self.message_user(request, f'{count} API keys regenerated.')
    regenerate_keys.short_description = 'Regenerate selected API keys'

    def deactivate_keys(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} API keys deactivated.')
    deactivate_keys.short_description = 'Deactivate selected API keys'


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type', 'url', 'is_active', 'success_count',
                    'failure_count', 'last_triggered']
    list_filter = ['event_type', 'is_active', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['secret_key', 'last_triggered', 'success_count',
                       'failure_count', 'created_at']

    actions = ['activate_webhooks', 'deactivate_webhooks']

    def activate_webhooks(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} webhooks activated.')
    activate_webhooks.short_description = 'Activate selected webhooks'

    def deactivate_webhooks(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} webhooks deactivated.')
    deactivate_webhooks.short_description = 'Deactivate selected webhooks'


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'success', 'response_code', 'triggered_at']
    list_filter = ['success', 'triggered_at']
    search_fields = ['webhook__name', 'error_message']
    readonly_fields = ['webhook', 'payload', 'response_code', 'response_body',
                       'success', 'error_message', 'triggered_at']
    date_hierarchy = 'triggered_at'

    def has_add_permission(self, request):
        return False  # Logs are created automatically


# ========== SUPPORT SYSTEM ==========

class SupportTicketReplyInline(admin.TabularInline):
    model = SupportTicketReply
    extra = 0
    readonly_fields = ['user', 'created_at']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'subject', 'user', 'category', 'priority',
                    'status', 'created_at']
    list_filter = ['category', 'priority', 'status', 'created_at']
    search_fields = ['ticket_id', 'subject', 'description', 'user__username']
    readonly_fields = ['ticket_id', 'created_at', 'updated_at', 'resolved_at']
    date_hierarchy = 'created_at'

    inlines = [SupportTicketReplyInline]

    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_id', 'user', 'subject', 'description')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'status', 'assigned_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at')
        }),
    )

    actions = ['mark_as_resolved', 'mark_as_closed']

    def mark_as_resolved(self, request, queryset):
        count = queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{count} tickets marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected as resolved'

    def mark_as_closed(self, request, queryset):
        count = queryset.update(status='closed')
        self.message_user(request, f'{count} tickets closed.')
    mark_as_closed.short_description = 'Close selected tickets'


# ========== HELP SYSTEM ==========

class HelpArticleInline(admin.TabularInline):
    model = HelpArticle
    extra = 0
    fields = ['title', 'is_published', 'views']
    readonly_fields = ['views']


@admin.register(HelpCategory)
class HelpCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'article_count']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [HelpArticleInline]

    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = 'Articles'


@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'is_published', 'views',
                    'helpful_count', 'created_at']
    list_filter = ['category', 'is_published', 'created_at']
    search_fields = ['title', 'content', 'summary']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views', 'helpful_count', 'not_helpful_count',
                       'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Article Information', {
            'fields': ('title', 'slug', 'category', 'summary')
        }),
        ('Content', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('Publishing', {
            'fields': ('author', 'is_published')
        }),
        ('Statistics', {
            'fields': ('views', 'helpful_count', 'not_helpful_count',
                      'created_at', 'updated_at')
        }),
    )

    actions = ['publish_articles', 'unpublish_articles']

    def publish_articles(self, request, queryset):
        count = queryset.update(is_published=True)
        self.message_user(request, f'{count} articles published.')
    publish_articles.short_description = 'Publish selected articles'

    def unpublish_articles(self, request, queryset):
        count = queryset.update(is_published=False)
        self.message_user(request, f'{count} articles unpublished.')
    unpublish_articles.short_description = 'Unpublish selected articles'


# ========== DASHBOARD ==========

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'widget_type', 'is_visible', 'order']
    list_filter = ['widget_type', 'is_visible']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at']


@admin.register(DashboardLayout)
class DashboardLayoutAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at']
