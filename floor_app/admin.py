from django.contrib import admin

from .hr.models import (
    HRPeople,
    HRPhone,
    HREmail,
    HRAddress,
    HREmployee,
    HRQualification,
    HREmployeeQualification,
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


class HRAddressInline(admin.TabularInline):
    model = HRAddress
    extra = 0
    autocomplete_fields = ("person",)

@admin.register(HRPeople)
class HRPeopleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "preferred_name_en",
        "first_name_en",
        "last_name_en",
        "national_id",
        "iqama_number",
    )
    search_fields = (
        "preferred_name_en",
        "first_name_en",
        "last_name_en",
        "national_id",
        "iqama_number",
    )
    # if your HRPeople fields are called something else, tweak these names


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


@admin.register(HRAddress)
class HRAddressAdmin(admin.ModelAdmin):
    list_display = ("address_line1", "city", "country_iso2", "kind", "use", "person")
    list_filter = ("kind", "use", "country_iso2")
    search_fields = ("address_line1", "city", "postal_code")
    autocomplete_fields = ("person",)


@admin.register(HREmployee)
class HREmployeeAdmin(admin.ModelAdmin):
    change_form_template = "admin/floor_app/hremployee/change_form.html"
    change_list_template = "admin/floor_app/hremployee/change_list.html"
    list_display = ("employee_no", "person", "job_title", "team", "status", "is_operator")
    list_filter = ("status", "team", "is_operator")
    search_fields = (
        "employee_no",
        "person__preferred_name_en",
        "person__first_name_en",
        "person__last_name_en",
    )

    autocomplete_fields = ("person", "user")


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


