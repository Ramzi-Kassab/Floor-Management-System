from django import forms
from django.contrib import admin
from ...hr.models.phone import HRPhone
from ..forms.widgets import CountrySelectWithCC
from ..forms.mixins import CountryCodeSyncMixin

class HRPhoneForm(CountryCodeSyncMixin):
    class Meta:
        model = HRPhone
        fields = "__all__"
        widgets = {
            "country_iso2": CountrySelectWithCC(),  # <-- instance (not the class)
            "calling_code": forms.TextInput(attrs={"readonly": "readonly"}),
        }

        class Media:
            js = ("hr/hr_admin.js",)  # path relative to the app's static/

    class Media:
        # ONE shared JS for all HR admin pages in this app
        js = ("hr/hr_admin.js",)

    def clean(self):
        cleaned = super().clean()
        # Landline ⇒ channel must be Call
        if cleaned.get("kind") == "LAND" and cleaned.get("channel") in {"WHATS", "BOTH"}:
            self.add_error("channel", "Landline can only be 'Call'.")
        return cleaned


@admin.register(HRPhone)
class HRPhoneAdmin(admin.ModelAdmin):
    form = HRPhoneForm
    list_display = ("phone_e164", "country_iso2", "calling_code", "kind", "channel", "use", "is_primary_hint", "is_deleted")
    list_filter  = ("kind", "channel", "use", "is_deleted", "country_iso2")
    search_fields = ("phone_e164", "national_number", "calling_code")
    readonly_fields = ("phone_e164", "created_at", "created_by", "updated_at", "updated_by")

    class Media:
        js = ("hr/hr_admin.js",)   # <- ALSO add here to guarantee inclusion

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
