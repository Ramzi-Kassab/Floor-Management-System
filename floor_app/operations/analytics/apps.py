from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.analytics'
    verbose_name = 'Analytics & Rule Engine'

    def ready(self):
        """Import signals when app is ready."""
        try:
            import floor_app.operations.analytics.signals  # noqa
        except ImportError:
            pass
