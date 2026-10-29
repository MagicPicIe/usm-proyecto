from django.urls import path

from . import views

app_name = 'empleos'

urlpatterns = [
    path('', views.mapa, name='mapa'),
    path('ofertas/<int:pk>/', views.detalle, name='detalle'),
    path('ofertas/<int:pk>/postular/', views.postular, name='postular'),
    path('api/ofertas/', views.api_ofertas, name='api_ofertas'),
]
