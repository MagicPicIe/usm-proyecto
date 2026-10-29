from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notificacion
from .preferencias import traspasar_test_de_sesion
from .telegram import enviar_en_segundo_plano, telegram_configurado


@receiver(user_logged_in)
def traspasar_test(sender, request, user, **kwargs):
    """Al iniciar sesión (o justo después de registrarse) se traspasa el test."""
    if request is not None:
        traspasar_test_de_sesion(request, user)


@receiver(post_save, sender=Notificacion)
def enviar_notificacion_telegram(sender, instance, created, **kwargs):
    """
    Cada notificación nueva se envía por Telegram si el usuario tiene el
    chat vinculado y las notificaciones activas. Cualquier error se ignora.
    """
    if not created or not telegram_configurado():
        return
    try:
        postulante = getattr(instance.usuario, 'postulante', None)
        if postulante and postulante.notificaciones_activas and postulante.telegram_chat_id:
            enviar_en_segundo_plano(postulante.telegram_chat_id, f'🔔 NexU\n{instance.mensaje}')
    except Exception:
        pass
