"""
Theme and appearance preferences for users

Provides:
- Light/Dark mode
- Color scheme preferences
- Font size preferences
- Accessibility settings
"""
from django.db import models
from django.contrib.auth.models import User


class UserThemePreference(models.Model):
    """
    User theme and appearance preferences
    """
    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
        ('auto', 'Auto (System Preference)'),
    ]

    COLOR_SCHEME_CHOICES = [
        ('blue', 'Blue (Default)'),
        ('green', 'Green'),
        ('purple', 'Purple'),
        ('orange', 'Orange'),
        ('red', 'Red'),
        ('teal', 'Teal'),
    ]

    FONT_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium (Default)'),
        ('large', 'Large'),
        ('xlarge', 'Extra Large'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='theme_preference'
    )

    # Theme settings
    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default='light'
    )

    color_scheme = models.CharField(
        max_length=20,
        choices=COLOR_SCHEME_CHOICES,
        default='blue'
    )

    # Typography
    font_size = models.CharField(
        max_length=20,
        choices=FONT_SIZE_CHOICES,
        default='medium'
    )

    # Accessibility
    high_contrast = models.BooleanField(
        default=False,
        help_text='Enable high contrast mode for better readability'
    )

    reduce_motion = models.BooleanField(
        default=False,
        help_text='Reduce animations and transitions'
    )

    # Layout preferences
    sidebar_collapsed = models.BooleanField(default=False)
    compact_mode = models.BooleanField(
        default=False,
        help_text='Use compact spacing for more content'
    )

    # Updated
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Theme Preference'
        verbose_name_plural = 'Theme Preferences'

    def __str__(self):
        return f"Theme for {self.user.username}"

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create theme preference for user"""
        preference, created = cls.objects.get_or_create(user=user)
        return preference

    def get_css_variables(self):
        """
        Get CSS variables for this theme

        Returns dict of CSS variable names and values
        """
        # Base colors for each scheme
        color_schemes = {
            'blue': {
                'primary': '#007bff',
                'primary-dark': '#0056b3',
                'primary-light': '#4da3ff',
            },
            'green': {
                'primary': '#28a745',
                'primary-dark': '#1e7e34',
                'primary-light': '#5cb85c',
            },
            'purple': {
                'primary': '#6f42c1',
                'primary-dark': '#5a32a3',
                'primary-light': '#9370db',
            },
            'orange': {
                'primary': '#fd7e14',
                'primary-dark': '#dc6502',
                'primary-light': '#ff9f40',
            },
            'red': {
                'primary': '#dc3545',
                'primary-dark': '#bd2130',
                'primary-light': '#e4606d',
            },
            'teal': {
                'primary': '#20c997',
                'primary-dark': '#199d76',
                'primary-light': '#5dd9b5',
            },
        }

        # Font sizes
        font_sizes = {
            'small': {
                'base': '13px',
                'large': '15px',
                'xlarge': '18px',
            },
            'medium': {
                'base': '14px',
                'large': '16px',
                'xlarge': '20px',
            },
            'large': {
                'base': '16px',
                'large': '18px',
                'xlarge': '22px',
            },
            'xlarge': {
                'base': '18px',
                'large': '20px',
                'xlarge': '24px',
            },
        }

        # Theme-specific colors
        if self.theme == 'dark':
            theme_colors = {
                'bg-primary': '#1a1a1a',
                'bg-secondary': '#2d2d2d',
                'bg-tertiary': '#3a3a3a',
                'text-primary': '#ffffff',
                'text-secondary': '#b0b0b0',
                'text-muted': '#808080',
                'border-color': '#404040',
            }
        else:  # light
            theme_colors = {
                'bg-primary': '#ffffff',
                'bg-secondary': '#f8f9fa',
                'bg-tertiary': '#e9ecef',
                'text-primary': '#212529',
                'text-secondary': '#6c757d',
                'text-muted': '#adb5bd',
                'border-color': '#dee2e6',
            }

        # High contrast adjustments
        if self.high_contrast:
            theme_colors['text-primary'] = '#000000' if self.theme == 'light' else '#ffffff'
            theme_colors['border-color'] = '#000000' if self.theme == 'light' else '#ffffff'

        # Combine all variables
        variables = {
            **color_schemes.get(self.color_scheme, color_schemes['blue']),
            **theme_colors,
            **font_sizes.get(self.font_size, font_sizes['medium']),
        }

        return variables
