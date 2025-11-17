from django.apps import AppConfig


class PurchasingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.purchasing'
    label = 'purchasing'
    verbose_name = 'Purchasing & Logistics'

    def ready(self):
        try:
            import floor_app.operations.purchasing.signals  # noqa
        except ImportError:
            pass
