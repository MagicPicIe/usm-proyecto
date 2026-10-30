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
]
