import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from empleos.opciones import (ANIOS_CARRERA, CATEGORIAS, COMUNAS, DIAS, JORNADAS,
                              RANGOS_PAGO, etiqueta)

from .validators import validar_rut


def generar_codigo_telegram():
    """Código aleatorio y único para vincular la cuenta con el bot."""
    return secrets.token_hex(8)


class Postulante(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='postulante', verbose_name='usuario')
    nombres = models.CharField('nombres', max_length=80)
    apellidos = models.CharField('apellidos', max_length=80)
    rut = models.CharField('RUT', max_length=12, unique=True, validators=[validar_rut])
    telefono = models.CharField('teléfono', max_length=20)
    comuna = models.CharField('comuna', max_length=20, choices=COMUNAS)
    notificaciones_activas = models.BooleanField('notificaciones activas', default=True)
    telegram_chat_id = models.CharField('chat ID de Telegram', max_length=32,
                                        blank=True, null=True)
    telegram_codigo = models.CharField('código de vinculación', max_length=32, unique=True,
                                       default=generar_codigo_telegram, editable=False)

    class Meta:
        verbose_name = 'postulante'
        verbose_name_plural = 'postulantes'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return self.nombre_completo

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    @property
    def iniciales(self):
        return (self.nombres[:1] + self.apellidos[:1]).upper()

    @property
    def telegram_vinculado(self):
        return bool(self.telegram_chat_id)

    def regenerar_codigo_telegram(self):
        self.telegram_codigo = generar_codigo_telegram()


class PreferenciasTest(models.Model):
    postulante = models.OneToOneField(Postulante, on_delete=models.CASCADE,
                                      related_name='preferencias', verbose_name='postulante')
    anio_carrera = models.CharField('año de carrera', max_length=12, choices=ANIOS_CARRERA)
    categorias = models.JSONField('categorías preferidas', default=list)
    jornadas = models.JSONField('jornadas preferidas', default=list)
    dias = models.JSONField('días disponibles', default=list)
    distancia_max = models.PositiveSmallIntegerField('distancia máxima (km)', default=5)
    pago_minimo = models.PositiveIntegerField('pago mínimo esperado (CLP)', default=0)
    fecha = models.DateTimeField('fecha de realización', default=timezone.now)

    class Meta:
        verbose_name = 'test de preferencias'
        verbose_name_plural = 'tests de preferencias'

    def __str__(self):
        return f'Test de {self.postulante}'

    def como_dict(self):
        """Formato que usan empleos/recomendaciones.py y la sesión del navegador."""
        return {
            'anio_carrera': self.anio_carrera,
            'categorias': list(self.categorias),
            'jornadas': list(self.jornadas),
            'dias': list(self.dias),
            'distancia_max': self.distancia_max,
            'pago_minimo': self.pago_minimo,
        }


def resumen_preferencias(prefs):
    """Convierte un diccionario de preferencias en textos legibles."""
    return [
        ('Año de carrera', etiqueta(ANIOS_CARRERA, prefs['anio_carrera'])),
        ('Trabajos que te interesan', ', '.join(etiqueta(CATEGORIAS, c) for c in prefs['categorias'])),
        ('Jornada', ', '.join(etiqueta(JORNADAS, j) for j in prefs['jornadas'])),
        ('Días disponibles', ', '.join(etiqueta(DIAS, d) for d in prefs['dias'])),
        ('Distancia máxima', f"{prefs['distancia_max']} km"),
        ('Pago mínimo', etiqueta(RANGOS_PAGO, prefs['pago_minimo'])
         if prefs['pago_minimo'] else 'Me da igual'),
    ]


class Notificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='notificaciones', verbose_name='usuario')
    mensaje = models.CharField('mensaje', max_length=300)
    leida = models.BooleanField('leída', default=False)
    fecha = models.DateTimeField('fecha', default=timezone.now)

    class Meta:
        verbose_name = 'notificación'
        verbose_name_plural = 'notificaciones'
        ordering = ['-fecha']

    def __str__(self):
        return self.mensaje[:60]

