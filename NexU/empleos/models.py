from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from cuentas.validators import validar_rut

from .linkedin import (normalizar_url_empleo, normalizar_url_empresa,
                       validar_url_empleo, validar_url_empresa)
from .opciones import (CATEGORIAS, COMUNAS, DIAS, EXPERIENCIAS, JORNADAS,
                       etiqueta, formatear_clp)


class PyME(models.Model):
    nombre = models.CharField('nombre', max_length=120)
    rut = models.CharField('RUT', max_length=12, unique=True, validators=[validar_rut])
    rubro = models.CharField('rubro', max_length=80)
    comuna = models.CharField('comuna', max_length=20, choices=COMUNAS)
    direccion = models.CharField('dirección', max_length=200)
    telefono = models.CharField('teléfono', max_length=20)
    correo = models.EmailField('correo')
    linkedin_url = models.URLField(
        'página de LinkedIn', max_length=500, blank=True, validators=[validar_url_empresa],
        help_text='Ej: https://www.linkedin.com/company/nombre-empresa/')

    class Meta:
        verbose_name = 'PyME'
        verbose_name_plural = 'PyMEs'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.linkedin_url = normalizar_url_empresa(self.linkedin_url) if self.linkedin_url else ''
        super().save(*args, **kwargs)


class OfertaTrabajo(models.Model):
    pyme = models.ForeignKey(PyME, on_delete=models.CASCADE, related_name='ofertas',
                             verbose_name='PyME')
    titulo = models.CharField('título', max_length=120)
    descripcion = models.TextField('descripción')
    categoria = models.CharField('categoría', max_length=20, choices=CATEGORIAS)
    pago = models.PositiveIntegerField('pago (CLP por jornada)')
    jornada = models.CharField('jornada', max_length=20, choices=JORNADAS)
    experiencia_requerida = models.CharField('experiencia requerida', max_length=10,
                                             choices=EXPERIENCIAS, default='sin')
    horario = models.CharField('horario', max_length=80, help_text='Ej: 09:00 a 14:00')
    # Lista de códigos de día, ej: ["lun", "mie", "vie"]
    dias = models.JSONField('días', default=list, blank=True)
    comuna = models.CharField('comuna', max_length=20, choices=COMUNAS)
    latitud = models.FloatField('latitud')
    longitud = models.FloatField('longitud')
    activa = models.BooleanField('activa', default=True)
    # --- Verificación con LinkedIn (ver empleos/linkedin.py) ---
    linkedin_url = models.URLField(
        'publicación en LinkedIn', max_length=500, blank=True, validators=[validar_url_empleo],
        help_text='Enlace a la misma oferta publicada en LinkedIn, '
                  'ej: https://www.linkedin.com/jobs/view/1234567890/')
    verificada = models.BooleanField(
        'verificada en LinkedIn', default=False,
        help_text='Márcala solo después de abrir el enlace y confirmar que la publicación '
                  'existe y corresponde a esta PyME.')
    fecha_verificacion = models.DateTimeField('fecha de verificación', null=True, blank=True)
    fecha_publicacion = models.DateTimeField('fecha de publicación', default=timezone.now)

    class Meta:
        verbose_name = 'oferta de trabajo'
        verbose_name_plural = 'ofertas de trabajo'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f'{self.titulo} ({self.pyme})'

    def get_absolute_url(self):
        return reverse('empleos:detalle', args=[self.pk])

    def clean(self):
        if self.verificada and not self.linkedin_url:
            raise ValidationError({'verificada': 'Para marcarla como verificada, primero agrega '
                                                 'el enlace de la publicación en LinkedIn.'})

    def save(self, *args, **kwargs):
        self.linkedin_url = normalizar_url_empleo(self.linkedin_url) if self.linkedin_url else ''
        # Si cambia el enlace de una oferta ya verificada, la verificación deja
        # de valer (se revisó otra publicación) y hay que volver a revisarla.
        if self.pk:
            anterior = OfertaTrabajo.objects.filter(pk=self.pk).values('linkedin_url', 'verificada').first()
            if anterior and anterior['verificada'] and anterior['linkedin_url'] != self.linkedin_url:
                self.verificada = False
        if not self.linkedin_url:
            self.verificada = False
        if self.verificada and self.fecha_verificacion is None:
            self.fecha_verificacion = timezone.now()
        if not self.verificada:
            self.fecha_verificacion = None
        super().save(*args, **kwargs)

    # --- Ayudas para mostrar datos en plantillas y JSON ---
    @property
    def pago_texto(self):
        return formatear_clp(self.pago)

    @property
    def dias_texto(self):
        orden = [codigo for codigo, _ in DIAS]
        dias = sorted(self.dias or [], key=lambda d: orden.index(d) if d in orden else 99)
        return ', '.join(etiqueta(DIAS, d) for d in dias) or 'A convenir'

    def como_dict_recomendacion(self):
        """Datos mínimos que necesita empleos/recomendaciones.py."""
        return {
            'categoria': self.categoria,
            'jornada': self.jornada,
            'dias': list(self.dias or []),
            'pago': self.pago,
            'experiencia': self.experiencia_requerida,
        }


class Postulacion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    postulante = models.ForeignKey('cuentas.Postulante', on_delete=models.CASCADE,
                                   related_name='postulaciones', verbose_name='postulante')
    oferta = models.ForeignKey(OfertaTrabajo, on_delete=models.CASCADE,
                               related_name='postulaciones', verbose_name='oferta')
    fecha = models.DateTimeField('fecha', default=timezone.now)
    estado = models.CharField('estado', max_length=10, choices=ESTADOS, default='pendiente')

    class Meta:
        verbose_name = 'postulación'
        verbose_name_plural = 'postulaciones'
        ordering = ['-fecha']
        constraints = [
            # Un postulante no puede postular dos veces a la misma oferta
            models.UniqueConstraint(fields=['postulante', 'oferta'],
                                    name='postulacion_unica'),
        ]

    def __str__(self):
        return f'{self.postulante} → {self.oferta.titulo}'
