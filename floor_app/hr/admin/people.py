from django.contrib import admin
from django.utils.html import format_html
from ..models.people import HRPeople

@admin.register(HRPeople)
class HRPeopleAdmin(admin.ModelAdmin):
    # Put display_name first so it’s the main link
    list_display = (
        "display_name", "gender", "primary_nationality_iso2",
        "date_of_birth", "date_of_birth_hijri",
        "national_id", "iqama_number", "is_deleted",
    )
    # Make the NAME the link to the change page
    list_display_links = ("display_name",)

    list_filter = ("gender", "primary_nationality_iso2", "is_deleted")
    search_fields = (
        "first_name_en", "middle_name_en", "last_name_en",
        "first_name_ar", "middle_name_ar", "last_name_ar",
        "preferred_name_en", "preferred_name_ar",
        "national_id", "iqama_number",
    )

    # Do not expose the internal hash
    readonly_fields = ("created_at", "created_by", "updated_at", "updated_by", "photo_preview")

    fieldsets = (
        ("Identity (English)", {"fields": (
            "first_name_en", "middle_name_en", "last_name_en", "preferred_name_en",
        )}),
        ("Identity (Arabic)", {"fields": (
            "first_name_ar", "middle_name_ar", "last_name_ar", "preferred_name_ar",
        )}),
        ("Demographics", {"fields": (
            "gender",
            "date_of_birth", "date_of_birth_hijri",
            "primary_nationality_iso2",
        )}),
        ("Legal IDs", {"fields": (
            ("national_id",),
            ("iqama_number", "iqama_expiry"),
        )}),
        ("Photo", {"fields": ("photo", "photo_preview")}),
        ("Audit", {"fields": ("created_at", "created_by", "updated_at", "updated_by")}),
    )

    class Media:
        js = (
            "https://cdn.jsdelivr.net/npm/moment@2.29.4/moment.min.js",
            "https://cdn.jsdelivr.net/npm/moment-hijri@2.1.2/moment-hijri.js",
            "hr/hr_people_dob_sync.js",
        )

    def display_name(self, obj):
        return obj.preferred_name_en or f"{obj.first_name_en} {obj.last_name_en}"
    display_name.short_description = "Name"

    def photo_preview(self, obj):
        if obj.photo and hasattr(obj.photo, "url"):
            return format_html('<img src="{}" style="max-width:140px; max-height:140px;border-radius:8px;" />', obj.photo.url)
        return "—"
    photo_preview.short_description = "Preview"

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

