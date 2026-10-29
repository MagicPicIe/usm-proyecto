"""Datos disponibles en todas las plantillas (encabezado del mapa)."""
from .telegram import telegram_configurado, url_vinculacion


def nexu(request):
    contexto = {'telegram_habilitado': telegram_configurado()}
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return contexto

    postulante = getattr(user, 'postulante', None)
    notificaciones = list(user.notificaciones.all()[:15])
    sin_leer = user.notificaciones.filter(leida=False).count()
    contexto.update({
        'postulante': postulante,
        'notificaciones': notificaciones,
        # Si desactivó las notificaciones, no se muestra el punto rojo
        'notificaciones_sin_leer': sin_leer if (postulante is None or postulante.notificaciones_activas) else 0,
        'telegram_url': url_vinculacion(postulante.telegram_codigo)
        if (postulante and telegram_configurado()) else '',
    })
    return contexto
