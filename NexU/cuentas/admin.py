from django.contrib import admin

from .models import Postulante, PreferenciasTest


class PreferenciasInline(admin.StackedInline):
    model = PreferenciasTest
    extra = 0


@admin.register(Postulante)
class PostulanteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut', 'correo', 'comuna', 'telefono')
    list_filter = ('comuna',)
    search_fields = ('nombres', 'apellidos', 'rut', 'usuario__email', 'telefono')
    inlines = [PreferenciasInline]

    @admin.display(description='correo')
    def correo(self, obj):
        return obj.usuario.email


@admin.register(PreferenciasTest)
class PreferenciasTestAdmin(admin.ModelAdmin):
    list_display = ('postulante', 'carrera', 'anio_carrera', 'distancia_max', 'pago_minimo', 'fecha')
    list_filter = ('anio_carrera', 'distancia_max')
    search_fields = ('postulante__nombres', 'postulante__apellidos', 'postulante__rut', 'carrera')
