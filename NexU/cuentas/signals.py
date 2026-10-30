from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .preferencias import traspasar_test_de_sesion


@receiver(user_logged_in)
def traspasar_test(sender, request, user, **kwargs):
    """Al iniciar sesión (o justo después de registrarse) se traspasa el test."""
    if request is not None:
        traspasar_test_de_sesion(request, user)
