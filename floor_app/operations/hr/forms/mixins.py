from django import forms
import phonenumbers

class CountryCodeSyncMixin(forms.ModelForm):
    """
    Prefills and enforces calling_code from country_iso2 on server side.
    """
    COUNTRY_FIELD = "country_iso2"
    CODE_FIELD = "calling_code"

    def _compute_code(self, iso):
        try:
            cc = phonenumbers.country_code_for_region(iso)
            return f"+{cc}" if cc else ""
        except Exception:
            return ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        iso = (self.initial.get(self.COUNTRY_FIELD)
               or (getattr(self.instance, self.COUNTRY_FIELD, "") if getattr(self.instance, "pk", None) else "")
               or "").upper()
        if iso:
            code = self._compute_code(iso)
            if code:
                self.fields[self.CODE_FIELD].initial = code

    def clean(self):
        cleaned = super().clean()
        iso = (cleaned.get(self.COUNTRY_FIELD) or "").upper()
        if iso:
            code = self._compute_code(iso)
            if code:
                cleaned[self.CODE_FIELD] = code
                setattr(self.instance, self.CODE_FIELD, code)
        return cleaned
