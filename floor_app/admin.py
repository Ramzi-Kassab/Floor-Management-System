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

    autocomplete_fields = ("person", "user", "position", "department", "report_to")
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
            "fields": ("employment_category", "report_to", "cost_center"),
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

