"""
Cliente mínimo de la API de Telegram usando solo urllib (librería estándar).

Todas las llamadas tienen timeout y capturan errores: si Telegram no responde
o el token es inválido, la página de NexU sigue funcionando normalmente.
"""
import json
import logging
import threading
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


def telegram_configurado():
    return bool(getattr(settings, 'TELEGRAM_BOT_TOKEN', '')) and \
        bool(getattr(settings, 'TELEGRAM_BOT_USERNAME', ''))


def url_vinculacion(codigo):
    """Enlace que abre el bot y le envía /start <codigo> al presionar Iniciar."""
    return f'https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={codigo}'


def llamar_api(metodo, datos=None, timeout=None):
    """
    Llama a https://api.telegram.org/bot<TOKEN>/<metodo> con datos JSON.
    Devuelve el campo 'result' o None si algo falla.
    """
    if not telegram_configurado():
        return None
    url = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{metodo}'
    cuerpo = json.dumps(datos or {}).encode('utf-8')
    peticion = urllib.request.Request(url, data=cuerpo,
                                      headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(peticion, timeout=timeout or settings.TELEGRAM_TIMEOUT) as resp:
            respuesta = json.loads(resp.read().decode('utf-8'))
            return respuesta.get('result') if respuesta.get('ok') else None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        logger.warning('Error al llamar a Telegram (%s): %s', metodo, error)
        return None


def enviar_mensaje(chat_id, texto):
    try:
        return llamar_api('sendMessage', {'chat_id': chat_id, 'text': texto})
    except Exception as error:  # Nunca debe romper la página
        logger.warning('No se pudo enviar el mensaje a Telegram: %s', error)
        return None


def enviar_en_segundo_plano(chat_id, texto):
    """Envía el mensaje en un hilo aparte para no hacer esperar al usuario."""
    hilo = threading.Thread(target=enviar_mensaje, args=(chat_id, texto), daemon=True)
    hilo.start()
