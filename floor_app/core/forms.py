"""
Forms for the core app
"""
from django import forms
from .theme_preferences import UserThemePreference


class UserThemePreferenceForm(forms.ModelForm):
    """Form for user theme and appearance preferences"""

    class Meta:
        model = UserThemePreference
        fields = [
            'theme',
            'color_scheme',
            'custom_background_color',
            'custom_text_color',
            'custom_primary_color',
            'font_size',
            'dyslexia_friendly',
            'high_contrast',
            'reduce_motion',
            'screen_reader_optimized',
            'sidebar_collapsed',
            'compact_mode',
        ]
        widgets = {
            'custom_background_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
            'custom_text_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
            'custom_primary_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
        }
