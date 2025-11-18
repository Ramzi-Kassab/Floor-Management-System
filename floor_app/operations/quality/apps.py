from django.apps import AppConfig


class QualityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.quality'
    label = 'quality'
    verbose_name = 'Quality Management'

    def ready(self):
        # Import signals if needed
        pass
