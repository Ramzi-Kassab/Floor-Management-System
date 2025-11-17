from django.apps import AppConfig


class ProductionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.production'
    label = 'production'
    verbose_name = 'Production & Evaluation'

    def ready(self):
        # Import signals if needed
        pass
