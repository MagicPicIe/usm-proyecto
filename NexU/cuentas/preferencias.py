"""
Manejo de las respuestas del test: en el perfil (usuarios con cuenta) o en la
sesión del navegador (visitantes sin cuenta).
"""
from django.utils import timezone

CLAVE_SESION = 'test_pendiente'


def obtener_postulante(user):
    if user.is_authenticated:
        return getattr(user, 'postulante', None)
    return None


def obtener_preferencias(request):
    """
    Devuelve las preferencias como diccionario, o None si no ha hecho el test.
    Primero se busca en el perfil; si no, en la sesión.
    """
    postulante = obtener_postulante(request.user)
    if postulante is not None:
        prefs = getattr(postulante, 'preferencias', None)
        if prefs is not None:
            return prefs.como_dict()
    datos = request.session.get(CLAVE_SESION)
    if datos:
        return {k: v for k, v in datos.items() if k != 'fecha'}
    return None


def guardar_en_perfil(postulante, datos):
    from .models import PreferenciasTest
    PreferenciasTest.objects.update_or_create(
        postulante=postulante,
        defaults={
            'anio_carrera': datos['anio_carrera'],
            'categorias': datos['categorias'],
            'jornadas': datos['jornadas'],
            'dias': datos['dias'],
            'distancia_max': datos['distancia_max'],
            'pago_minimo': datos['pago_minimo'],
            'fecha': timezone.now(),
        },
    )


def traspasar_test_de_sesion(request, user):
    """
    Si el visitante hizo el test sin cuenta, al registrarse o iniciar sesión
    sus respuestas pasan automáticamente al perfil. Devuelve True si traspasó.
    """
    datos = request.session.get(CLAVE_SESION)
    postulante = getattr(user, 'postulante', None)
    if not datos or postulante is None:
        return False
    guardar_en_perfil(postulante, datos)
    del request.session[CLAVE_SESION]
    return True
