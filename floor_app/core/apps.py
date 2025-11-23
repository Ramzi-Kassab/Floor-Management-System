"""
Core app configuration
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.core'
    verbose_name = 'Core System'

    def ready(self):
        """
        Import signal handlers and perform app initialization
        """
        # Import signals to register them
        try:
            from . import middleware  # This registers the signal handlers
        except ImportError:
            pass

        # Create custom permissions
        try:
            from .permissions import create_custom_permissions
            # Note: This will be called during migrations
            # create_custom_permissions()
        except Exception:
            pass
