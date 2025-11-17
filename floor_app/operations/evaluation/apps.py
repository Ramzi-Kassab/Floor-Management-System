from django.apps import AppConfig


class EvaluationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.evaluation'
    label = 'evaluation'
    verbose_name = 'Evaluation & Technical Instructions'

    def ready(self):
        # Import signals if needed
        pass
