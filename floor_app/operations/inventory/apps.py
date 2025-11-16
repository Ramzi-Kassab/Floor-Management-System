from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'

    # Full Python path to the app package
    name = 'floor_app.operations.inventory'

    # This makes Django know this app as "inventory" for things like 'inventory.Item'
    label = 'inventory'

    verbose_name = 'Inventory & Materials Management'

    def ready(self):
        # Import signals to register them (if any)
        pass
