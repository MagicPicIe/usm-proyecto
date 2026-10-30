import re

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

from empleos.opciones import (ANIOS_CARRERA, CARRERAS, CATEGORIAS, COMUNAS, DIAS, JORNADAS,
                              RANGOS_PAGO)

from .models import Postulante
from .validators import formatear_rut, validar_rut


class LoginForm(forms.Form):
    # Acepta el correo o el nombre de usuario (ej: el usuario de prueba "nexusprueba")
    correo = forms.CharField(label='Correo o usuario', max_length=150, widget=forms.TextInput(attrs={
        'autocomplete': 'username', 'placeholder': 'tu@correo.cl', 'autofocus': True,
        'autocapitalize': 'none', 'spellcheck': 'false'}))
    contrasena = forms.CharField(label='Contraseña', strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'current-password', 'placeholder': 'Tu contraseña'}))

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.usuario = None
        super().__init__(*args, **kwargs)

    def clean(self):
        datos = super().clean()
        correo, contrasena = datos.get('correo'), datos.get('contrasena')
        if correo and contrasena:
            # EmailBackend lo prueba como correo y ModelBackend como nombre de usuario
            self.usuario = authenticate(self.request, username=correo.strip(), password=contrasena)
            if self.usuario is None:
                raise forms.ValidationError(
                    'El correo (o usuario) o la contraseña no son correctos. Revisa ambos e intenta de nuevo.')
        return datos


class RegistroForm(forms.Form):
    nombres = forms.CharField(label='Nombres', max_length=80,
                              widget=forms.TextInput(attrs={'autocomplete': 'given-name'}))
    apellidos = forms.CharField(label='Apellidos', max_length=80,
                                widget=forms.TextInput(attrs={'autocomplete': 'family-name'}))
    rut = forms.CharField(label='RUT', max_length=12,
                          widget=forms.TextInput(attrs={'placeholder': '12.345.678-9'}))
    correo = forms.EmailField(label='Correo',
                              widget=forms.EmailInput(attrs={'autocomplete': 'email'}))
    telefono = forms.CharField(label='Teléfono', max_length=20, widget=forms.TextInput(
        attrs={'placeholder': '+56 9 1234 5678', 'autocomplete': 'tel'}))
    comuna = forms.ChoiceField(label='Comuna', choices=COMUNAS)
    contrasena = forms.CharField(label='Contraseña', strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'new-password'}))
    contrasena2 = forms.CharField(label='Confirmar contraseña', strip=False,
                                  widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        validar_rut(rut)
        rut = formatear_rut(rut)
        if Postulante.objects.filter(rut=rut).exists():
            raise forms.ValidationError('Ya existe una cuenta con este RUT.')
        return rut

    def clean_correo(self):
        correo = self.cleaned_data['correo'].strip().lower()
        if get_user_model().objects.filter(email__iexact=correo).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo. ¿Quieres iniciar sesión?')
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono']
        digitos = re.sub(r'\D', '', telefono)
        if not 8 <= len(digitos) <= 12:
            raise forms.ValidationError('Ingresa un teléfono válido, por ejemplo +56 9 1234 5678.')
        return telefono.strip()

    def clean(self):
        datos = super().clean()
        c1, c2 = datos.get('contrasena'), datos.get('contrasena2')
        if c1 and c2 and c1 != c2:
            self.add_error('contrasena2', 'Las contraseñas no coinciden.')
        elif c1:
            usuario_temporal = get_user_model()(
                username=datos.get('correo', ''), email=datos.get('correo', ''),
                first_name=datos.get('nombres', ''), last_name=datos.get('apellidos', ''))
            try:
                validate_password(c1, usuario_temporal)
            except forms.ValidationError as error:
                self.add_error('contrasena', error)
        return datos


class TestPreferenciasForm(forms.Form):
    """Valida las respuestas del test (la interfaz de 1 pregunta por pantalla es JS)."""
    carrera = forms.ChoiceField(choices=CARRERAS, error_messages={
        'required': 'Elige la carrera que estudias.'})
    anio_carrera = forms.ChoiceField(choices=ANIOS_CARRERA,
                                     error_messages={'required': 'Indica tu año de carrera.'})
    categorias = forms.MultipleChoiceField(choices=CATEGORIAS, error_messages={
        'required': 'Elige al menos un tipo de trabajo.'})
    jornadas = forms.MultipleChoiceField(choices=JORNADAS, error_messages={
        'required': 'Elige al menos una jornada.'})
    dias = forms.MultipleChoiceField(choices=DIAS, error_messages={
        'required': 'Elige al menos un día disponible.'})
    distancia_max = forms.IntegerField(min_value=1, max_value=20)
    pago_minimo = forms.TypedChoiceField(choices=RANGOS_PAGO, coerce=int)
