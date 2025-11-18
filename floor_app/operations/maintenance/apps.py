from django.apps import AppConfig


class MaintenanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.maintenance'
    label = 'maintenance'
    verbose_name = 'Maintenance & Assets'

    def ready(self):
        import floor_app.operations.maintenance.signals  # noqa
