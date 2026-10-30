from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from empleos.opciones import (ANIOS_CARRERA, CARRERAS, CATEGORIAS, DIAS, JORNADAS,
                              RANGOS_PAGO)

from .forms import LoginForm, RegistroForm, TestPreferenciasForm
from .models import Postulante, PreferenciasTest, resumen_preferencias
from .preferencias import (CLAVE_SESION, guardar_en_perfil, obtener_postulante,
                           obtener_preferencias)


def _destino_seguro(request, por_defecto='empleos:mapa'):
    siguiente = request.POST.get('next') or request.GET.get('next')
    if siguiente and url_has_allowed_host_and_scheme(
            siguiente, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return siguiente
    return por_defecto


@never_cache
def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('empleos:mapa')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.usuario)  # authenticate() ya indicó qué backend lo validó
        return redirect(_destino_seguro(request))
    return render(request, 'cuentas/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
        'test_en_sesion': CLAVE_SESION in request.session,
    })


@never_cache
def registro(request):
    if request.user.is_authenticated:
        return redirect('empleos:mapa')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            usuario = get_user_model().objects.create_user(
                username=d['correo'], email=d['correo'], password=d['contrasena'],
                first_name=d['nombres'], last_name=d['apellidos'])
            Postulante.objects.create(
                usuario=usuario, nombres=d['nombres'], apellidos=d['apellidos'],
                rut=d['rut'], telefono=d['telefono'], comuna=d['comuna'])
        # login() dispara la señal que traspasa el test hecho sin cuenta
        login(request, usuario, backend='cuentas.backends.EmailBackend')
        messages.success(request, f'¡Bienvenido/a a NexU, {d["nombres"]}!')
        if PreferenciasTest.objects.filter(postulante__usuario=usuario).exists():
            return redirect('empleos:mapa')
        return redirect('cuentas:invitar_test')
    return render(request, 'cuentas/registro.html', {'form': form})


@require_POST
def cerrar_sesion(request):
    logout(request)
    return redirect('cuentas:login')


@login_required
def invitar_test(request):
    return render(request, 'cuentas/invitar_test.html')


@never_cache
def test_preferencias(request):
    """Test de 7 preguntas. Funciona con o sin cuenta."""
    previas = obtener_preferencias(request) or {}
    if request.method == 'POST':
        form = TestPreferenciasForm(request.POST)
        if form.is_valid():
            datos = dict(form.cleaned_data)
            postulante = obtener_postulante(request.user)
            if postulante is not None:
                guardar_en_perfil(postulante, datos)
            else:
                # Sin cuenta: se guarda en la sesión hasta que inicie sesión
                datos['fecha'] = timezone.now().isoformat()
                request.session[CLAVE_SESION] = datos
            return redirect('cuentas:test_resumen')
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
        previas = {k: request.POST.getlist(k) if k in ('categorias', 'jornadas', 'dias')
                   else request.POST.get(k) for k in form.fields}

    return render(request, 'cuentas/test.html', {
        'carreras': CARRERAS,
        'anios': ANIOS_CARRERA,
        'categorias': CATEGORIAS,
        'jornadas': JORNADAS,
        'dias': DIAS,
        'rangos_pago': RANGOS_PAGO,
        'previas': previas,
        'distancia_inicial': previas.get('distancia_max') or 5,
    })


def test_resumen(request):
    prefs = obtener_preferencias(request)
    if prefs is None:
        return redirect('cuentas:test')
    return render(request, 'cuentas/test_resumen.html', {
        'resumen': resumen_preferencias(prefs),
    })


def csrf_fallido(request, reason=''):
    """
    Reemplaza la página 403 "La verificación CSRF ha fallado".

    Pasa cuando se envía un formulario con un token viejo, por ejemplo:
    - se presionó Atrás después de iniciar sesión y se volvió a enviar;
    - se inició o cerró sesión en otra pestaña (Django cambia el token);
    - otro proyecto Django en 127.0.0.1 sobrescribió la cookie csrftoken.

    En vez de un error, se vuelve a la página anterior (que ya trae un token
    nuevo) con un aviso. No se ejecuta la acción original, así que es seguro.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': False, 'mensaje': 'La página estaba desactualizada. '
                             'Recárgala (F5) e intenta de nuevo.'}, status=403)
    messages.warning(request, 'La página estaba desactualizada y la recargamos. '
                              'Intenta de nuevo.')
    volver = request.META.get('HTTP_REFERER', '')
    if volver and url_has_allowed_host_and_scheme(
            volver, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(volver)
    return redirect('empleos:mapa')
