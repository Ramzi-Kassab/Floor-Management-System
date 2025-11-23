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

    # Custom Colors (overrides color_scheme if set)
    custom_background_color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        help_text='Custom background color in hex format (e.g., #ffffff)'
    )

    custom_text_color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        help_text='Custom text color in hex format (e.g., #000000)'
    )

    custom_primary_color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        help_text='Custom primary/accent color in hex format (e.g., #007bff)'
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

        # Apply custom colors (override defaults)
        if self.custom_background_color:
            variables['bg-primary'] = self.custom_background_color
            # Generate lighter/darker shades for secondary and tertiary
            variables['bg-secondary'] = self._adjust_brightness(self.custom_background_color, 0.05)
            variables['bg-tertiary'] = self._adjust_brightness(self.custom_background_color, 0.1)

        if self.custom_text_color:
            variables['text-primary'] = self.custom_text_color
            # Generate lighter shades for secondary and muted text
            variables['text-secondary'] = self._adjust_opacity(self.custom_text_color, 0.7)
            variables['text-muted'] = self._adjust_opacity(self.custom_text_color, 0.5)

        if self.custom_primary_color:
            variables['primary'] = self.custom_primary_color
            variables['primary-dark'] = self._adjust_brightness(self.custom_primary_color, -0.15)
            variables['primary-light'] = self._adjust_brightness(self.custom_primary_color, 0.15)

        return variables

    def _adjust_brightness(self, hex_color, percent):
        """
        Adjust brightness of a hex color by a percentage

        Args:
            hex_color: Hex color string (e.g., '#ff0000')
            percent: Percentage to adjust (-1.0 to 1.0, negative for darker, positive for lighter)

        Returns:
            Adjusted hex color string
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Adjust brightness
        if percent > 0:
            # Lighten
            r = int(r + (255 - r) * percent)
            g = int(g + (255 - g) * percent)
            b = int(b + (255 - b) * percent)
        else:
            # Darken
            r = int(r * (1 + percent))
            g = int(g * (1 + percent))
            b = int(b * (1 + percent))

        # Clamp values
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'

    def _adjust_opacity(self, hex_color, opacity):
        """
        Convert hex color to rgba with opacity

        Args:
            hex_color: Hex color string (e.g., '#ff0000')
            opacity: Opacity value (0.0 to 1.0)

        Returns:
            RGBA color string
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return f'rgba({r}, {g}, {b}, {opacity})'
