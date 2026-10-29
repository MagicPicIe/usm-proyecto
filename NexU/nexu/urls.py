"""Rutas principales de NexU: cada app define las suyas con include()."""
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Administración NexU'
admin.site.site_title = 'NexU'
admin.site.index_title = 'Panel de administración'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuentas/', include('cuentas.urls')),
    path('', include('empleos.urls')),
]
