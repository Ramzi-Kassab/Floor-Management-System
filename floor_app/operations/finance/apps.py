"""
Finance App Configuration
"""
from django.apps import AppConfig


class FinanceConfig(AppConfig):
    """Configuration for Finance operations app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.finance'
    verbose_name = 'Finance - Cost & Impact Tracking'

    def ready(self):
        """Import signals when app is ready."""
        # Import signals here when needed
        pass
