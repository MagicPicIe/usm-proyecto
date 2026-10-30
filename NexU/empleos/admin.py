from django import forms
from django.contrib import admin

from .models import OfertaTrabajo, Postulacion, PyME
from .opciones import DIAS


class OfertaTrabajoForm(forms.ModelForm):
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
    list_display = ('nombre', 'rut', 'rubro', 'comuna', 'telefono', 'correo')
    list_filter = ('comuna', 'rubro')
    search_fields = ('nombre', 'rut', 'rubro', 'correo')
    inlines = [OfertaInline]


@admin.register(OfertaTrabajo)
class OfertaTrabajoAdmin(admin.ModelAdmin):
    form = OfertaTrabajoForm
    list_display = ('titulo', 'pyme', 'categoria', 'jornada', 'experiencia_requerida',
                    'pago', 'comuna', 'activa', 'fecha_publicacion')
    list_filter = ('activa', 'categoria', 'jornada', 'experiencia_requerida', 'comuna')
    search_fields = ('titulo', 'descripcion', 'pyme__nombre')
    list_editable = ('activa',)


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = ('postulante', 'oferta', 'pyme', 'fecha', 'estado')
    list_filter = ('estado', 'oferta__categoria', 'oferta__pyme')
    search_fields = ('postulante__nombres', 'postulante__apellidos', 'postulante__rut',
                     'oferta__titulo', 'oferta__pyme__nombre')
    list_editable = ('estado',)
    actions = ['marcar_aceptada', 'marcar_rechazada']

    @admin.display(description='PyME')
    def pyme(self, obj):
        return obj.oferta.pyme

    def _cambiar_estado(self, request, queryset, estado):
        total = queryset.update(estado=estado)
        self.message_user(request, f'{total} postulación(es) actualizada(s).')

    @admin.action(description='Marcar como aceptadas')
    def marcar_aceptada(self, request, queryset):
        self._cambiar_estado(request, queryset, 'aceptada')

    @admin.action(description='Marcar como rechazadas')
    def marcar_rechazada(self, request, queryset):
        self._cambiar_estado(request, queryset, 'rechazada')
