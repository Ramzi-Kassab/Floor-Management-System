from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.analytics'
    verbose_name = 'Analytics & Activity Monitoring'

    def ready(self):
        import floor_app.operations.analytics.signals
