from django.contrib import admin

from .models import Notificacion, Postulante, PreferenciasTest


class PreferenciasInline(admin.StackedInline):
    model = PreferenciasTest
    extra = 0


@admin.register(Postulante)
class PostulanteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut', 'correo', 'comuna', 'telefono',
                    'notificaciones_activas', 'telegram_conectado')
    list_filter = ('comuna', 'notificaciones_activas')
    search_fields = ('nombres', 'apellidos', 'rut', 'usuario__email', 'telefono')
    readonly_fields = ('telegram_codigo',)
    inlines = [PreferenciasInline]

    @admin.display(description='correo')
    def correo(self, obj):
        return obj.usuario.email

    @admin.display(description='Telegram', boolean=True)
    def telegram_conectado(self, obj):
        return obj.telegram_vinculado


@admin.register(PreferenciasTest)
class PreferenciasTestAdmin(admin.ModelAdmin):
    list_display = ('postulante', 'anio_carrera', 'distancia_max', 'pago_minimo', 'fecha')
    list_filter = ('anio_carrera', 'distancia_max')
    search_fields = ('postulante__nombres', 'postulante__apellidos', 'postulante__rut')


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'mensaje', 'leida', 'fecha')
    list_filter = ('leida', 'fecha')
    search_fields = ('usuario__email', 'usuario__username', 'mensaje')
