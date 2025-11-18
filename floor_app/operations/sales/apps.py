from django.apps import AppConfig


class SalesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.sales'
    label = 'sales'
    verbose_name = 'Sales, Lifecycle & Drilling Operations'

    def ready(self):
        # Import signals if needed
        pass
