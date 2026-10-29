"""Backend de autenticación que permite iniciar sesión con el correo."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        correo = email or username
        if not correo or password is None:
            return None
        User = get_user_model()
        usuario = User.objects.filter(email__iexact=correo.strip()).order_by('id').first()
        if usuario is None:
            # Ejecuta el hasher igual para no revelar por tiempo si el correo existe
            User().set_password(password)
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
