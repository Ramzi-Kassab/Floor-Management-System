"""
Retrieval System App Configuration
"""

from django.apps import AppConfig


class RetrievalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.retrieval'
    verbose_name = 'Retrieval/Undo System'

    def ready(self):
        """
        Import signals and perform app initialization.
        """
        # Import signals here if needed
        pass
