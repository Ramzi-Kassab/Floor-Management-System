from django.apps import AppConfig


class HRConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'

    # Full Python path to the app package
    name = 'floor_app.operations.hr'

    # 👉 This is the important part:
    # This makes Django know this app as "hr" for things like 'hr.HRPeople'
    label = 'hr'

    verbose_name = 'HR & Administration'

    def ready(self):
        # Import signals to register them
        import floor_app.operations.hr.signals  # noqa

