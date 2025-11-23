"""
Floor Management System initialization

This ensures Celery app is loaded when Django starts.
"""
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed - this is okay for development/testing
    __all__ = ()
    pass
