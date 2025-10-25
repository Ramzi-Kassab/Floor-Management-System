from django import forms
import phonenumbers

class CountrySelectWithCC(forms.Select):
    """
    Adds data-cc="+NNN" to each <option> so our single JS can sync the calling code.
    """
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value:
            try:
                cc = phonenumbers.country_code_for_region(str(value))
                if cc:
                    option["attrs"]["data-cc"] = f"+{cc}"
            except Exception:
                pass
        return option
