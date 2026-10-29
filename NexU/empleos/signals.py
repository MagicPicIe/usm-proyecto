"""
Señales de empleos: crean una Notificacion cuando alguien postula y cada vez
que cambia el estado de una postulación (por ejemplo, desde el admin).
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from cuentas.models import Notificacion

from .models import Postulacion


@receiver(pre_save, sender=Postulacion)
def recordar_estado_anterior(sender, instance, **kwargs):
    """Antes de guardar, anota el estado que había en la base de datos."""
    if instance.pk:
        anterior = Postulacion.objects.filter(pk=instance.pk).values_list('estado', flat=True).first()
        instance._estado_anterior = anterior
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Postulacion)
def notificar_postulacion(sender, instance, created, **kwargs):
    usuario = instance.postulante.usuario
    oferta = instance.oferta
    if created:
        Notificacion.objects.create(
            usuario=usuario,
            mensaje=f'Postulaste a "{oferta.titulo}" en {oferta.pyme.nombre}. '
                    f'Te avisaremos cuando la PyME responda.',
        )
        return

    anterior = getattr(instance, '_estado_anterior', None)
    if anterior and anterior != instance.estado:
        textos = {
            'aceptada': '¡Buenas noticias! Tu postulación a "{t}" en {p} fue aceptada.',
            'rechazada': 'Tu postulación a "{t}" en {p} no fue seleccionada esta vez.',
            'pendiente': 'Tu postulación a "{t}" en {p} volvió a quedar pendiente.',
        }
        Notificacion.objects.create(
            usuario=usuario,
            mensaje=textos[instance.estado].format(t=oferta.titulo, p=oferta.pyme.nombre),
        )
