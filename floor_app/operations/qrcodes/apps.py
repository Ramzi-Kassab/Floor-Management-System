from django.apps import AppConfig


class QRCodesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'floor_app.operations.qrcodes'
    label = 'qrcodes'
    verbose_name = 'QR Codes & Scanning'

    def ready(self):
        # Import signal handlers if any
        pass
