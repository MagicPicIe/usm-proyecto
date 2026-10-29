from django import forms
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import OfertaTrabajo, Postulacion, PyME
from .opciones import DIAS


class OfertaTrabajoForm(forms.ModelForm):
    # En el admin los días se eligen con casillas en vez de escribir JSON
    dias = forms.MultipleChoiceField(choices=DIAS, required=False,
                                     widget=forms.CheckboxSelectMultiple, label='Días')

    class Meta:
        model = OfertaTrabajo
        fields = '__all__'


class OfertaInline(admin.TabularInline):
    model = OfertaTrabajo
    fields = ('titulo', 'categoria', 'jornada', 'pago', 'activa')
    extra = 0
    show_change_link = True


@admin.register(PyME)
class PyMEAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'rubro', 'comuna', 'telefono', 'correo', 'ver_linkedin')
    list_filter = ('comuna', 'rubro')
    search_fields = ('nombre', 'rut', 'rubro', 'correo')
    inlines = [OfertaInline]

    @admin.display(description='LinkedIn')
    def ver_linkedin(self, obj):
        if not obj.linkedin_url:
            return '—'
        return format_html('<a href="{}" target="_blank" rel="noopener">Abrir</a>', obj.linkedin_url)


@admin.register(OfertaTrabajo)
class OfertaTrabajoAdmin(admin.ModelAdmin):
    form = OfertaTrabajoForm
    list_display = ('titulo', 'pyme', 'categoria', 'jornada', 'experiencia_requerida',
                    'pago', 'comuna', 'activa', 'ver_linkedin', 'verificada', 'fecha_publicacion')
    list_filter = ('activa', 'verificada', 'categoria', 'jornada', 'experiencia_requerida', 'comuna')
    search_fields = ('titulo', 'descripcion', 'pyme__nombre', 'linkedin_url')
    list_editable = ('activa',)
    readonly_fields = ('fecha_verificacion',)
    actions = ['marcar_verificada', 'quitar_verificacion']

    @admin.display(description='LinkedIn')
    def ver_linkedin(self, obj):
        # Enlace para que el admin abra la publicación y la revise antes de verificar
        if not obj.linkedin_url:
            return '—'
        return format_html('<a href="{}" target="_blank" rel="noopener">Abrir</a>', obj.linkedin_url)

    @admin.action(description='Marcar como verificadas (ya revisé la publicación en LinkedIn)')
    def marcar_verificada(self, request, queryset):
        con_enlace = queryset.exclude(linkedin_url='')
        sin_enlace = queryset.count() - con_enlace.count()
        for oferta in con_enlace:
            oferta.verificada = True
            oferta.fecha_verificacion = timezone.now()
            oferta.save()
        mensaje = f'{con_enlace.count()} oferta(s) verificada(s).'
        if sin_enlace:
            mensaje += f' {sin_enlace} no se verificaron porque no tienen enlace de LinkedIn.'
        self.message_user(request, mensaje)

    @admin.action(description='Quitar verificación')
    def quitar_verificacion(self, request, queryset):
        for oferta in queryset:
            oferta.verificada = False
            oferta.save()
        self.message_user(request, f'{queryset.count()} oferta(s) quedaron sin verificar.')


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = ('postulante', 'oferta', 'pyme', 'fecha', 'estado')
    list_filter = ('estado', 'oferta__categoria', 'oferta__pyme')
    search_fields = ('postulante__nombres', 'postulante__apellidos', 'postulante__rut',
                     'oferta__titulo', 'oferta__pyme__nombre')
    # El estado se cambia directo desde la lista; al guardar se dispara la
    # señal que crea la notificación (y el aviso por Telegram).
    list_editable = ('estado',)
    actions = ['marcar_aceptada', 'marcar_rechazada']

    @admin.display(description='PyME')
    def pyme(self, obj):
        return obj.oferta.pyme

    def _cambiar_estado(self, request, queryset, estado):
        # Se guarda una por una (no queryset.update) para que se disparen las señales
        for postulacion in queryset:
            postulacion.estado = estado
            postulacion.save()
        self.message_user(request, f'{queryset.count()} postulación(es) actualizada(s).')

    @admin.action(description='Marcar como aceptadas')
    def marcar_aceptada(self, request, queryset):
        self._cambiar_estado(request, queryset, 'aceptada')

    @admin.action(description='Marcar como rechazadas')
    def marcar_rechazada(self, request, queryset):
        self._cambiar_estado(request, queryset, 'rechazada')
