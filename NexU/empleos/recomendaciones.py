"""
Cálculo de recomendaciones de NexU.

Este archivo NO depende de Django: recibe datos simples (diccionarios y
números) para que cada función se pueda probar por separado.

FÓRMULA GENERAL (resultado de 0 a 100):

    puntaje = 0.70 × puntaje_preferencias + 0.30 × puntaje_cercania

puntaje_preferencias (0 a 100) suma cinco criterios, cada uno vale entre 0 y 1
y se multiplica por su peso:

    Categoría preferida ............ 35 %
    Jornada preferida .............. 25 %
    Días disponibles compatibles ... 15 %
    Pago vs. mínimo esperado ....... 15 %
    Experiencia acorde a la carrera  10 %

puntaje_cercania (0 a 100): vale 100 si la oferta está justo en la ubicación
del usuario y baja en línea recta hasta 0 cuando la distancia llega a la
distancia máxima que el usuario indicó en el test.

Ejemplo: categoría sí (35), jornada sí (25), 2 de 3 días (10), pago sobre el
mínimo (15) y experiencia acorde (10) => preferencias = 95. Si está a 2 km y
su máximo es 10 km => cercanía = 80. Total = 0.7·95 + 0.3·80 = 90.5 -> 91.

Las ofertas con 70 puntos o más se marcan como "Recomendadas".
"""
from math import asin, cos, radians, sin, sqrt

# --- Constantes de la fórmula --------------------------------------------
PESO_PREFERENCIAS = 0.70
PESO_CERCANIA = 0.30

PESO_CATEGORIA = 0.35
PESO_JORNADA = 0.25
PESO_DIAS = 0.15
PESO_PAGO = 0.15
PESO_EXPERIENCIA = 0.10

UMBRAL_RECOMENDADA = 70

# Si el pago está bajo el mínimo pero a menos de un 20 % de él, recibe
# puntaje parcial (ej: pide $25.000 y la oferta paga $22.000).
TOLERANCIA_PAGO = 0.20

RADIO_TIERRA_KM = 6371.0


# --- Distancia ------------------------------------------------------------
def haversine_km(lat1, lng1, lat2, lng2):
    """
    Distancia en kilómetros entre dos puntos (latitud/longitud en grados)
    usando la fórmula de Haversine, que considera la curvatura de la Tierra.
    Se usa en lugar de GeoDjango/PostGIS para no depender de librerías extra.
    """
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * RADIO_TIERRA_KM * asin(sqrt(a))


# --- Criterios individuales (cada uno devuelve un valor entre 0 y 1) ------
def puntaje_categoria(categoria_oferta, categorias_preferidas):
    """1 si la categoría de la oferta está entre las preferidas; si no, 0."""
    return 1.0 if categoria_oferta in categorias_preferidas else 0.0


def puntaje_jornada(jornada_oferta, jornadas_preferidas):
    """1 si la jornada de la oferta está entre las preferidas; si no, 0."""
    return 1.0 if jornada_oferta in jornadas_preferidas else 0.0


def puntaje_dias(dias_oferta, dias_disponibles):
    """
    Proporción de los días de la oferta que el usuario tiene disponibles.
    Ej: la oferta es lun-mie-vie y el usuario puede lun y vie -> 2/3.
    Si la oferta no indica días, se considera compatible (1).
    """
    if not dias_oferta:
        return 1.0
    coinciden = len(set(dias_oferta) & set(dias_disponibles))
    return coinciden / len(set(dias_oferta))


def puntaje_pago(pago_oferta, pago_minimo):
    """
    1 si el pago es igual o mayor al mínimo esperado (o si no hay mínimo).
    Si está bajo el mínimo, pero dentro del 20 % de tolerancia, el puntaje
    baja en línea recta: justo en el mínimo vale 1 y en el 80 % del mínimo
    vale 0. Bajo eso, 0.
    """
    if pago_minimo <= 0 or pago_oferta >= pago_minimo:
        return 1.0
    piso = pago_minimo * (1 - TOLERANCIA_PAGO)
    if pago_oferta <= piso:
        return 0.0
    return (pago_oferta - piso) / (pago_minimo - piso)


def experiencias_permitidas(anio_carrera):
    """
    Niveles de experiencia acordes al año de carrera:
      1° y 2°             -> solo 'sin' experiencia
      3° y 4°             -> hasta 'baja'
      5°+ o egresado/a    -> todas
      no estudia          -> todas (puede tener experiencia laboral previa)
    """
    if anio_carrera in ('1', '2'):
        return {'sin'}
    if anio_carrera in ('3', '4'):
        return {'sin', 'baja'}
    return {'sin', 'baja', 'alta'}


def puntaje_experiencia(experiencia_oferta, anio_carrera):
    """1 si la experiencia pedida es acorde al año de carrera; si no, 0."""
    return 1.0 if experiencia_oferta in experiencias_permitidas(anio_carrera) else 0.0


def puntaje_cercania(distancia_km, distancia_maxima_km):
    """
    100 en la ubicación del usuario, baja linealmente y llega a 0 en su
    distancia máxima. Más lejos que eso también es 0.
    """
    if distancia_maxima_km <= 0:
        return 0.0
    return max(0.0, 100.0 * (1 - distancia_km / distancia_maxima_km))


# --- Combinación ----------------------------------------------------------
def puntaje_preferencias(oferta, prefs):
    """
    Suma ponderada de los cinco criterios, escalada a 0-100.
    `oferta` y `prefs` son diccionarios (ver docstring de calcular_puntaje).
    """
    total = (
        PESO_CATEGORIA * puntaje_categoria(oferta['categoria'], prefs['categorias'])
        + PESO_JORNADA * puntaje_jornada(oferta['jornada'], prefs['jornadas'])
        + PESO_DIAS * puntaje_dias(oferta['dias'], prefs['dias'])
        + PESO_PAGO * puntaje_pago(oferta['pago'], prefs['pago_minimo'])
        + PESO_EXPERIENCIA * puntaje_experiencia(oferta['experiencia'], prefs['anio_carrera'])
    )
    return 100.0 * total


def calcular_puntaje(oferta, prefs, distancia_km):
    """
    Puntaje final de compatibilidad (entero de 0 a 100).

    oferta: {'categoria', 'jornada', 'dias' (lista), 'pago', 'experiencia'}
    prefs:  {'categorias', 'jornadas', 'dias' (listas), 'pago_minimo',
             'anio_carrera', 'distancia_max'}
    """
    pref = puntaje_preferencias(oferta, prefs)
    cerca = puntaje_cercania(distancia_km, prefs['distancia_max'])
    # Redondeo tradicional (90.5 -> 91); round() de Python redondea al par.
    return int(PESO_PREFERENCIAS * pref + PESO_CERCANIA * cerca + 0.5)


def es_recomendada(puntaje):
    """Una oferta es recomendada si su puntaje es 70 o más."""
    return puntaje is not None and puntaje >= UMBRAL_RECOMENDADA
