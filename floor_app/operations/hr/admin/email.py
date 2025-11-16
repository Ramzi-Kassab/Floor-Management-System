from django import forms
from django.contrib import admin
from ..models.email import HREmail

class HREmailForm(forms.ModelForm):
    class Meta:
        model = HREmail
        fields = "__all__"

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip().lower()

@admin.register(HREmail)
class HREmailAdmin(admin.ModelAdmin):
    form = HREmailForm
    list_display = ("email", "kind", "is_verified", "is_primary_hint", "is_deleted")
    list_filter  = ("kind", "is_verified", "is_deleted")
    search_fields = ("email",)
    readonly_fields = ("created_at", "created_by", "updated_at", "updated_by")

    def save_model(self, request, obj, form, change):
        if not getattr(obj, "created_by_id", None):
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
