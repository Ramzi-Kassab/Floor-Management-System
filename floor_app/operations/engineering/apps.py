from django.apps import AppConfig


class EngineeringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.engineering'
    label = 'engineering'  # Short label for migrations - must match ForeignKey references
    verbose_name = 'Engineering - Design & BOM'

    def ready(self):
        """Import signals when app is ready."""
        # import floor_app.operations.engineering.signals  # Uncomment when signals are needed
        pass
