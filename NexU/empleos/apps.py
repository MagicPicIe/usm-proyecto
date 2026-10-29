from django.apps import AppConfig


class EmpleosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'empleos'
    verbose_name = 'Empleos'

    def ready(self):
        # Registra las señales (notificaciones al postular / cambiar estado)
        from . import signals  # noqa: F401
