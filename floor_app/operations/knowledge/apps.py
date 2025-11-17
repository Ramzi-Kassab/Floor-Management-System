from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.knowledge'
    label = 'knowledge'
    verbose_name = 'Knowledge & Instructions'

    def ready(self):
        # Import signals to register them
        import floor_app.operations.knowledge.signals  # noqa
