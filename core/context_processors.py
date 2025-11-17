"""
Context processors for the core app.
Injects user preferences and global settings into all templates.
"""

from .models import UserPreference


def user_preferences(request):
    """
    Injects user preference settings into template context.
    This allows templates to access theme, font_size, and table_density.
    """
    context = {
        'theme': 'light',
        'font_size': 'normal',
        'table_density': 'normal',
        'sidebar_collapsed': False,
        'user_preferences': None,
    }

    if request.user.is_authenticated:
        try:
            pref = UserPreference.get_or_create_for_user(request.user)
            context.update({
                'theme': pref.theme,
                'font_size': pref.font_size,
                'table_density': pref.table_density,
                'sidebar_collapsed': pref.sidebar_collapsed,
                'user_preferences': pref,
            })
        except Exception:
            # If there's any issue, use defaults
            pass

    return context


def global_settings(request):
    """
    Injects global application settings into template context.
    """
    return {
        'app_name': 'Floor Management System',
        'app_version': '2.0.0',
        'app_copyright_year': '2025',
    }
