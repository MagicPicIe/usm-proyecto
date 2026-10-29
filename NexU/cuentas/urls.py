from django.urls import path

from . import views

app_name = 'cuentas'

urlpatterns = [
    path('login/', views.iniciar_sesion, name='login'),
    path('registro/', views.registro, name='registro'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('test/', views.test_preferencias, name='test'),
    path('test/resumen/', views.test_resumen, name='test_resumen'),
    path('test/invitacion/', views.invitar_test, name='invitar_test'),
    path('notificaciones/leer/', views.marcar_notificaciones_leidas, name='notificaciones_leer'),
    path('configuracion/notificaciones/', views.cambiar_notificaciones, name='config_notificaciones'),
    path('telegram/desconectar/', views.desconectar_telegram, name='telegram_desconectar'),
]
