from django.apps import AppConfig


class CuentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cuentas'
    verbose_name = 'Cuentas'

    def ready(self):
        # Señales: traspaso del test al iniciar sesión y envío a Telegram
        from . import signals  # noqa: F401
