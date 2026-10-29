"""
python manage.py telegram_bot

Ejecuta el bot de NexU con "long polling": pregunta a Telegram cada pocos
segundos si hay mensajes nuevos (getUpdates). No usa webhooks, así que
funciona en un computador local sin dominio público.

Debe correr en una terminal aparte mientras runserver corre en otra.
"""
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from cuentas.models import Postulante
from cuentas.telegram import enviar_mensaje, llamar_api, telegram_configurado
from empleos import recomendaciones as rec
from empleos.models import OfertaTrabajo
from empleos.opciones import COORDENADAS_COMUNAS, formatear_clp

AYUDA = (
    'Comandos de NexU:\n'
    '/postulaciones – tus postulaciones y su estado\n'
    '/recomendados – los 5 trabajos más compatibles contigo\n'
    '/ayuda – muestra este mensaje\n\n'
    'Las novedades de tus postulaciones te llegarán aquí automáticamente.'
)

NO_VINCULADO = (
    'Este chat aún no está conectado a una cuenta NexU.\n\n'
    'Para conectarlo: entra a NexU, abre Configuraciones (el engranaje) y '
    'presiona "Conectar Telegram". Se abrirá este chat; luego presiona Iniciar.'
)

ESTADOS = {'pendiente': '⏳ Pendiente', 'aceptada': '✅ Aceptada', 'rechazada': '❌ Rechazada'}


class Command(BaseCommand):
    help = 'Ejecuta el bot de Telegram de NexU (long polling).'

    def handle(self, *args, **options):
        if not telegram_configurado():
            self.stderr.write(self.style.ERROR(
                'Falta configurar el bot. Copia nexu/config_local.ejemplo.py como '
                'nexu/config_local.py y completa TELEGRAM_BOT_TOKEN y TELEGRAM_BOT_USERNAME.'))
            return

        yo = llamar_api('getMe')
        if not yo:
            self.stderr.write(self.style.ERROR(
                'No se pudo conectar con Telegram. Revisa el token y tu conexión a internet.'))
            return
        # Si alguna vez se configuró un webhook, getUpdates no funciona; se borra.
        llamar_api('deleteWebhook')
        self.stdout.write(self.style.SUCCESS(
            f"Bot @{yo.get('username')} escuchando mensajes. Presiona Ctrl+C para detenerlo."))

        offset = None
        try:
            while True:
                datos = {'timeout': 25, 'allowed_updates': ['message']}
                if offset is not None:
                    datos['offset'] = offset
                # timeout de urllib mayor que el de Telegram para no cortar la espera
                actualizaciones = llamar_api('getUpdates', datos, timeout=35)
                if actualizaciones is None:
                    time.sleep(3)  # error de red: esperar y reintentar
                    continue
                for update in actualizaciones:
                    offset = update['update_id'] + 1
                    mensaje = update.get('message') or {}
                    texto = (mensaje.get('text') or '').strip()
                    chat_id = (mensaje.get('chat') or {}).get('id')
                    if chat_id and texto:
                        close_old_connections()
                        try:
                            respuesta = self.procesar(str(chat_id), texto)
                        except Exception as error:  # un error no detiene el bot
                            self.stderr.write(f'Error procesando mensaje: {error}')
                            respuesta = 'Ocurrió un error al procesar tu mensaje. Intenta de nuevo.'
                        enviar_mensaje(chat_id, respuesta)
                        self.stdout.write(f'[{chat_id}] {texto}')
        except KeyboardInterrupt:
            self.stdout.write('\nBot detenido.')

    # --- Lógica de comandos ---------------------------------------------
    def procesar(self, chat_id, texto):
        partes = texto.split(maxsplit=1)
        # "/postulaciones@NexUBot" -> "/postulaciones"
        comando = partes[0].split('@')[0].lower()
        argumento = partes[1].strip() if len(partes) > 1 else ''

        if comando == '/start':
            return self.vincular(chat_id, argumento)
        if comando in ('/ayuda', '/help'):
            return AYUDA

        postulante = Postulante.objects.filter(telegram_chat_id=chat_id).first()
        if postulante is None:
            return NO_VINCULADO
        if comando == '/postulaciones':
            return self.listar_postulaciones(postulante)
        if comando == '/recomendados':
            return self.listar_recomendados(postulante)
        return 'No conozco ese comando.\n\n' + AYUDA

    def vincular(self, chat_id, codigo):
        if not codigo:
            ya = Postulante.objects.filter(telegram_chat_id=chat_id).first()
            if ya:
                return f'Hola {ya.nombres}, tu cuenta NexU ya está conectada.\n\n' + AYUDA
            return NO_VINCULADO
        postulante = Postulante.objects.filter(telegram_codigo=codigo).first()
        if postulante is None:
            return ('El código de conexión no es válido o ya expiró. Vuelve a presionar '
                    '"Conectar Telegram" en NexU.')
        # Un chat solo puede estar conectado a una cuenta
        Postulante.objects.filter(telegram_chat_id=chat_id).exclude(pk=postulante.pk) \
            .update(telegram_chat_id=None)
        postulante.telegram_chat_id = chat_id
        postulante.save(update_fields=['telegram_chat_id'])
        return f'Tu cuenta NexU quedó conectada ✅\nHola, {postulante.nombres}.\n\n' + AYUDA

    def listar_postulaciones(self, postulante):
        postulaciones = postulante.postulaciones.select_related('oferta__pyme')[:15]
        if not postulaciones:
            return 'Aún no tienes postulaciones. Busca trabajos en el mapa de NexU y postula.'
        lineas = ['Tus postulaciones:\n']
        for p in postulaciones:
            lineas.append(f'• {p.oferta.titulo} – {p.oferta.pyme.nombre}\n  {ESTADOS[p.estado]}')
        return '\n'.join(lineas)

    def listar_recomendados(self, postulante):
        prefs = getattr(postulante, 'preferencias', None)
        if prefs is None:
            return ('Aún no haces el test de preferencias. Hazlo en NexU '
                    '(Configuraciones > Repetir test) para recibir recomendaciones.')
        prefs = prefs.como_dict()
        # En Telegram no hay GPS: se usa la comuna del perfil como ubicación
        lat, lng = COORDENADAS_COMUNAS.get(postulante.comuna, COORDENADAS_COMUNAS['valparaiso'])
        evaluadas = []
        for oferta in OfertaTrabajo.objects.filter(activa=True).select_related('pyme'):
            distancia = rec.haversine_km(lat, lng, oferta.latitud, oferta.longitud)
            puntaje = rec.calcular_puntaje(oferta.como_dict_recomendacion(), prefs, distancia)
            evaluadas.append((puntaje, distancia, oferta))
        evaluadas.sort(key=lambda t: (-t[0], t[1]))
        lineas = [f'Tus 5 trabajos más compatibles (desde {postulante.get_comuna_display()}):\n']
        for puntaje, distancia, oferta in evaluadas[:5]:
            estrella = '⭐ ' if rec.es_recomendada(puntaje) else ''
            lineas.append(
                f'{estrella}{oferta.titulo} – {oferta.pyme.nombre}\n'
                f'  {formatear_clp(oferta.pago)} · {distancia:.1f} km · {puntaje}% compatible'
                + (' · ✓ verificada en LinkedIn' if oferta.verificada else ''))
        return '\n'.join(lineas)
