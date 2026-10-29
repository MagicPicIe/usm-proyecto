"""
Verificación de ofertas con LinkedIn.

LinkedIn NO ofrece una API pública para consultar si una oferta existe: su
API de empleos (Talent Solutions / Job Posting) es solo para socios aprobados
por LinkedIn, y leer sus páginas con un programa va contra sus condiciones.

Por eso NexU usa una verificación manual y transparente:
  1. La PyME (o el admin) pega el enlace de la publicación en LinkedIn.
  2. Este archivo valida que el enlace sea realmente de LinkedIn y lo deja
     en formato estándar (https://www.linkedin.com/jobs/view/<id>/).
  3. El administrador abre el enlace, confirma que la publicación existe y
     corresponde a la PyME, y marca la oferta como "Verificada".
  4. El postulante ve el sello y puede abrir la publicación él mismo.
"""
import re
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError

EJEMPLO_EMPLEO = 'https://www.linkedin.com/jobs/view/1234567890/'
EJEMPLO_EMPRESA = 'https://www.linkedin.com/company/nombre-empresa/'


def _es_linkedin(url):
    """True si la URL es http(s) y su dominio es linkedin.com o un subdominio (cl.linkedin.com)."""
    partes = urlparse((url or '').strip())
    host = (partes.hostname or '').lower()
    return partes.scheme in ('http', 'https') and (host == 'linkedin.com' or host.endswith('.linkedin.com'))


def id_empleo(url):
    """
    Extrae el número de la publicación. Acepta los formatos que entrega LinkedIn:
      /jobs/view/1234567890/
      /jobs/view/garzon-en-cafe-1234567890
      /jobs/search/?currentJobId=1234567890   (y /jobs/collections/...)
    Devuelve None si el enlace no es de una oferta de LinkedIn.
    """
    if not _es_linkedin(url):
        return None
    partes = urlparse(url.strip())
    m = re.match(r'^/jobs/view/(?:[^/]*-)?(\d{5,})/?$', partes.path.rstrip('/') + '/')
    if m:
        return m.group(1)
    actual = parse_qs(partes.query).get('currentJobId', [''])[0]
    if partes.path.startswith('/jobs/') and actual.isdigit():
        return actual
    return None


def slug_empresa(url):
    """Extrae el identificador de la página de empresa: /company/<slug>/."""
    if not _es_linkedin(url):
        return None
    m = re.match(r'^/company/([^/?#]+)', urlparse(url.strip()).path)
    return m.group(1) if m else None


def normalizar_url_empleo(url):
    numero = id_empleo(url)
    return f'https://www.linkedin.com/jobs/view/{numero}/' if numero else url


def normalizar_url_empresa(url):
    slug = slug_empresa(url)
    return f'https://www.linkedin.com/company/{slug}/' if slug else url


def validar_url_empleo(url):
    if url and id_empleo(url) is None:
        raise ValidationError(
            f'Pega el enlace de una publicación de empleo de LinkedIn, por ejemplo {EJEMPLO_EMPLEO}')


def validar_url_empresa(url):
    if url and slug_empresa(url) is None:
        raise ValidationError(
            f'Pega el enlace de la página de empresa en LinkedIn, por ejemplo {EJEMPLO_EMPRESA}')
