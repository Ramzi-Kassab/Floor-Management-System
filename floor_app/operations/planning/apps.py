from django.apps import AppConfig


class PlanningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.planning'
    label = 'planning'
    verbose_name = 'Planning & KPI Management'

    def ready(self):
        # Import signals if needed
        pass
