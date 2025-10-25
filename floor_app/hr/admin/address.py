from django import forms
from django.contrib import admin
from ..models.address import HRAddress
from ..forms.widgets import CountrySelectWithCC

class HRAddressForm(forms.ModelForm):
    full_address = forms.CharField(
        required=False,
        label="Search/Full Address",
        help_text="Type to search; pick from the map, then adjust fields below."
    )

    class Meta:
        model = HRAddress
        fields = "__all__"
        widgets = {"country_iso2": CountrySelectWithCC()}

    class Media:
        css = {"all": ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",)}
        js = (
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
            "hr/hr_address_admin.js",
        )

@admin.register(HRAddress)
class HRAddressAdmin(admin.ModelAdmin):
    form = HRAddressForm

    list_display  = (
        "address_line1", "street_name", "building_number", "neighborhood",
        "city", "postal_code", "country_iso2", "latitude", "longitude",
        "address_kind", "kind", "use", "is_deleted"
    )
    list_filter   = ("country_iso2", "kind", "use", "address_kind", "is_deleted")
    search_fields = (
        "address_line1", "address_line2", "street_name", "building_number",
        "neighborhood", "city", "state_region", "postal_code"
    )
    readonly_fields = ("created_at", "created_by", "updated_at", "updated_by")

    fieldsets = (
        (None, {"fields": ("full_address",)}),
        ("Address (free-form)", {"fields": (
            "address_line1", "address_line2", "city", "state_region", "postal_code", "country_iso2",
        )}),
        ("Structured / National (KSA-ready)", {"fields": (
            "address_kind", "street_name", "building_number", "unit_number",
            "neighborhood", "additional_number", "po_box",
        )}),
        ("Location", {"fields": ("latitude", "longitude")}),
        ("Usage", {"fields": ("kind", "use", "label", "is_primary_hint")}),
        ("Audit", {"fields": ("created_at", "created_by", "updated_at", "updated_by")}),
    )

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
