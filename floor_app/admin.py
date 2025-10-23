# floor_app/admin.py
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

from .models import (
    # owners
    Employee, Customer, Supplier, Carrier, Company, Address, AddressLink,
    # contacts
    Contact, ContactMethod,
)


# -------------------------
# Base admin with audit UX
# -------------------------
class AuditAdmin(admin.ModelAdmin):
    """
    Makes created_at/updated_at/created_by/updated_by readonly,
    and auto-fills created_by/updated_by on save.
    """
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, "created_by_id") and obj.created_by_id is None:
            obj.created_by = request.user if request.user.is_authenticated else None
        if hasattr(obj, "updated_by_id"):
            obj.updated_by = request.user if request.user.is_authenticated else None
        super().save_model(request, obj, form, change)


class AddressLinkInline(admin.TabularInline):
    model = AddressLink
    extra = 0
    fields = ("type", "label", "is_primary", "sequence", "owner_content_type", "owner_object_id")
    readonly_fields = ("owner_content_type", "owner_object_id")
    ordering = ("type", "sequence")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    inlines = [AddressLinkInline]

    list_display = (
        "address_id", "country_code", "region", "city",
        "neighborhood", "street_name", "building_no", "postal_code",
    )
    list_filter = ("country_code", "region", "city", "neighborhood")
    search_fields = (
        "street_name", "building_no", "additional_no", "unit_no",
        "neighborhood", "city", "region", "postal_code",
        "line1", "line2", "po_box",
    )
    ordering = ("country_code", "region", "city", "neighborhood", "street_name", "building_no")



# ---------------------------------------
# Contact + ContactMethod (detail screen)
# ---------------------------------------
class ContactMethodInline(admin.TabularInline):
    model = ContactMethod
    extra = 1
    fields = ("kind", "email", "e164_phone", "is_primary", "is_whatsapp", "label")
    ordering = ("kind", "-is_primary", "label")


@admin.register(Contact)
class ContactAdmin(AuditAdmin):
    list_display = (
        "display_name", "kind", "party_type", "party_id",
        "is_primary", "updated_at"
    )
    list_filter = ("kind", "is_primary", "party_type")
    search_fields = (
        "first_name", "middle_name", "last_name", "company_name",
        "methods__email", "methods__e164_phone"
    )
    inlines = [ContactMethodInline]


# ----------------------------------------------------
# Generic Inline to add Contacts on each owner’s page
# ----------------------------------------------------
class ContactInline(GenericTabularInline):
    """
    Lets you add Contact rows (person/company) directly on the owner page.
    Click the change link to add ContactMethods (emails/phones/WhatsApp).
    """
    model = Contact
    ct_field = "party_type"
    ct_fk_field = "party_id"
    extra = 1
    fields = (
        "kind",
        "first_name", "middle_name", "last_name",
        "company_name",
        "job_title",
        "is_primary",
        "notes",
    )
    show_change_link = True
    ordering = ("-is_primary", "kind", "last_name", "first_name")


# ------------------------
# Employee (with contacts)
# ------------------------
@admin.register(Employee)
class EmployeeAdmin(AuditAdmin):
    inlines = [ContactInline]

    list_display = (
        "employee_code", "first_name", "last_name",
        "designation", "department", "employment_status",
        "allow_admin_login",
        "updated_at"
    )
    list_filter = ("designation", "department", "employment_status", "allow_admin_login")
    search_fields = ("employee_code", "first_name", "last_name")


# ------------------------
# Customer (with contacts)
# ------------------------
@admin.register(Customer)
class CustomerAdmin(AuditAdmin):
    inlines = [ContactInline]

    list_display = ("code", "name", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("code", "name")


# ------------------------
# Supplier (with contacts)
# ------------------------
@admin.register(Supplier)
class SupplierAdmin(AuditAdmin):
    inlines = [ContactInline]

    list_display = ("code", "name", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("code", "name")


# -----------------------
# Carrier (with contacts)
# -----------------------
@admin.register(Carrier)
class CarrierAdmin(AuditAdmin):
    inlines = [ContactInline]

    list_display = ("code", "name", "mode", "is_active")
    list_filter = ("mode", "is_active")
    search_fields = ("code", "name")


# -----------------------
# Company (with contacts)
# -----------------------
@admin.register(Company)
class CompanyAdmin(AuditAdmin):
    inlines = [ContactInline]

    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")

