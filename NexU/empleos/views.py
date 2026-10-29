from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from cuentas.preferencias import obtener_postulante, obtener_preferencias

from . import recomendaciones as rec
from .models import OfertaTrabajo, Postulacion
from .opciones import (COMUNAS, COORDENADAS_COMUNAS, EXPERIENCIAS, JORNADAS,
                       etiqueta)

UBICACION_POR_DEFECTO = COORDENADAS_COMUNAS['valparaiso']


def _lista_parametro(request, nombre, validos):
    """
    Lee filtros que pueden venir repetidos (?jornada=diurna&jornada=nocturna)
    o separados por coma (?jornada=diurna,nocturna). Ignora valores inválidos.
    """
    valores = []
    for crudo in request.GET.getlist(nombre):
        valores += [v.strip() for v in crudo.split(',') if v.strip()]
    return [v for v in valores if v in validos]


def _float(valor, por_defecto):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return por_defecto


def evaluar_ofertas(ofertas, lat, lng, radio_km, prefs, postuladas=()):
    """
    Calcula distancia y puntaje de cada oferta y deja solo las que están
    dentro del radio. Devuelve una lista de diccionarios listos para JSON,
    ordenada por puntaje (mayor primero) y luego por cercanía.
    """
    resultado = []
    for oferta in ofertas:
        distancia = rec.haversine_km(lat, lng, oferta.latitud, oferta.longitud)
        if distancia > radio_km:
            continue
        puntaje = None
        if prefs:
            puntaje = rec.calcular_puntaje(oferta.como_dict_recomendacion(), prefs, distancia)
        resultado.append({
            'id': oferta.pk,
            'titulo': oferta.titulo,
            'pyme': oferta.pyme.nombre,
            'categoria': oferta.categoria,
            'categoria_texto': oferta.get_categoria_display(),
            'pago': oferta.pago,
            'pago_texto': oferta.pago_texto,
            'jornada': oferta.jornada,
            'jornada_texto': oferta.get_jornada_display(),
            'experiencia': oferta.experiencia_requerida,
            'experiencia_texto': oferta.get_experiencia_requerida_display(),
            'horario': oferta.horario,
            'dias_texto': oferta.dias_texto,
            'comuna': oferta.get_comuna_display(),
            'lat': oferta.latitud,
            'lng': oferta.longitud,
            'distancia_km': round(distancia, 2),
            'puntaje': puntaje,
            'recomendada': rec.es_recomendada(puntaje),
            'ya_postulo': oferta.pk in postuladas,
            'verificada': oferta.verificada,
            'linkedin_url': oferta.linkedin_url,
            'linkedin_empresa': oferta.pyme.linkedin_url,
            'url_detalle': oferta.get_absolute_url(),
            'url_postular': reverse('empleos:postular', args=[oferta.pk]),
        })
    resultado.sort(key=lambda o: (-(o['puntaje'] or 0), o['distancia_km']))
    return resultado


def _ids_postulados(user):
    postulante = obtener_postulante(user)
    if postulante is None:
        return set()
    return set(postulante.postulaciones.values_list('oferta_id', flat=True))


def api_ofertas(request):
    """
    GET /api/ofertas/?lat=-33.04&lng=-71.61&radio=5&jornada=diurna,part_time
                     &experiencia=sin,baja&recomendados=1

    Devuelve las ofertas activas dentro del radio con distancia y puntaje.
    Se puede abrir directo en el navegador para demostrar cómo cambian los
    resultados al modificar los parámetros.
    """
    lat = _float(request.GET.get('lat'), UBICACION_POR_DEFECTO[0])
    lng = _float(request.GET.get('lng'), UBICACION_POR_DEFECTO[1])
    radio = min(max(_float(request.GET.get('radio'), 5), 1), 20)
    jornadas = _lista_parametro(request, 'jornada', dict(JORNADAS))
    experiencias = _lista_parametro(request, 'experiencia', dict(EXPERIENCIAS))
    solo_recomendados = request.GET.get('recomendados') in ('1', 'true', 'si')
    solo_verificadas = request.GET.get('verificadas') in ('1', 'true', 'si')

    ofertas = OfertaTrabajo.objects.filter(activa=True).select_related('pyme')
    if jornadas:
        ofertas = ofertas.filter(jornada__in=jornadas)
    if experiencias:
        ofertas = ofertas.filter(experiencia_requerida__in=experiencias)
    if solo_verificadas:
        ofertas = ofertas.filter(verificada=True)

    prefs = obtener_preferencias(request)
    lista = evaluar_ofertas(ofertas, lat, lng, radio, prefs, _ids_postulados(request.user))
    if solo_recomendados and prefs:
        lista = [o for o in lista if o['recomendada']]

    datos = {
        'parametros': {
            'lat': lat, 'lng': lng, 'radio_km': radio,
            'jornada': jornadas, 'experiencia': experiencias,
            'recomendados': solo_recomendados,
            'verificadas': solo_verificadas,
        },
        'test_realizado': prefs is not None,
        'umbral_recomendada': rec.UMBRAL_RECOMENDADA,
        'total': len(lista),
        'total_recomendadas': sum(1 for o in lista if o['recomendada']),
        'ofertas': lista,
    }
    # indent y ensure_ascii=False para que se lea bien al abrirlo en el navegador
    return JsonResponse(datos, json_dumps_params={'ensure_ascii': False, 'indent': 2})


@never_cache
@login_required
def mapa(request):
    """Pantalla principal: solo el mapa con los trabajos como marcadores."""
    prefs = obtener_preferencias(request)
    postulante = obtener_postulante(request.user)

    # Filtros precargados con las preferencias del test (si existe)
    filtros_iniciales = {
        'radio': prefs['distancia_max'] if prefs else 5,
        'jornada': prefs['jornadas'] if prefs else [],
        'experiencia': sorted(rec.experiencias_permitidas(prefs['anio_carrera'])) if prefs else [],
        'recomendados': False,
        'verificadas': False,
    }
    config_mapa = {
        'api': reverse('empleos:api_ofertas'),
        'test_realizado': prefs is not None,
        'filtros': filtros_iniciales,
        'comunas': [
            {'codigo': c, 'nombre': n, 'lat': COORDENADAS_COMUNAS[c][0], 'lng': COORDENADAS_COMUNAS[c][1]}
            for c, n in COMUNAS
        ],
        'comuna_perfil': postulante.comuna if postulante else 'valparaiso',
        'proveedor_mapa': getattr(settings, 'MAPA_PROVEEDOR', 'osm'),
    }
    return render(request, 'empleos/mapa.html', {
        'config_mapa': config_mapa,
        'jornadas': JORNADAS,
        'experiencias': EXPERIENCIAS,
        'test_realizado': prefs is not None,
    })


@never_cache
@login_required
def detalle(request, pk):
    oferta = get_object_or_404(OfertaTrabajo.objects.select_related('pyme'), pk=pk)
    postulante = obtener_postulante(request.user)
    ya_postulo = bool(postulante) and Postulacion.objects.filter(
        postulante=postulante, oferta=oferta).exists()
    return render(request, 'empleos/detalle.html', {
        'oferta': oferta,
        'ya_postulo': ya_postulo,
        'experiencia_texto': etiqueta(EXPERIENCIAS, oferta.experiencia_requerida),
    })


@require_POST
def postular(request, pk):
    """
    POST /ofertas/<id>/postular/ (con el token CSRF en el header X-CSRFToken).
    Responde JSON para mostrar el aviso flotante sin recargar el mapa.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'mensaje': 'Inicia sesión para postular.'}, status=401)
    postulante = obtener_postulante(request.user)
    if postulante is None:
        return JsonResponse({'ok': False, 'mensaje': 'Tu usuario no tiene perfil de postulante. '
                             'Crea una cuenta desde el registro para postular.'}, status=400)
    oferta = get_object_or_404(OfertaTrabajo, pk=pk, activa=True)
    _, creada = Postulacion.objects.get_or_create(postulante=postulante, oferta=oferta)
    if creada:
        return JsonResponse({'ok': True, 'ya_postulo': True,
                             'mensaje': f'Postulaste a {oferta.titulo}'})
    return JsonResponse({'ok': True, 'ya_postulo': True,
                         'mensaje': 'Ya postulaste a esta oferta'})
