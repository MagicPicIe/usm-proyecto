"""
Configuración del proyecto NexU.

Nota: el ramo pedía Django 5.1.1, pero esa versión no soporta Python 3.14.
Por eso el proyecto usa Django 5.2 LTS (ver requirements.txt).
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Clave solo para desarrollo local (proyecto universitario).
SECRET_KEY = 'django-insecure-nexu-usm-cambiar-en-produccion-7f3k2m9x'
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'nexu.localhost', 'nexu.usm']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps propias
    'cuentas.apps.CuentasConfig',
    'empleos.apps.EmpleosConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nexu.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # templates/ en la raíz solo contiene base.html; el resto vive en
        # <app>/templates/<app>/
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Datos del encabezado: notificaciones, avatar, Telegram
                'cuentas.context_processors.nexu',
            ],
        },
    },
]

WSGI_APPLICATION = 'nexu.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Se inicia sesión con correo: primero se prueba nuestro backend por email y
# luego el normal de Django (para que el admin siga funcionando con username).
AUTHENTICATION_BACKENDS = [
    'cuentas.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Si un formulario llega con un token CSRF viejo, en vez de la página 403
# se recarga la página con un aviso (ver cuentas/views.py: csrf_fallido).
CSRF_FAILURE_VIEW = 'cuentas.views.csrf_fallido'

LOGIN_URL = 'cuentas:login'
LOGIN_REDIRECT_URL = 'empleos:mapa'
LOGOUT_REDIRECT_URL = 'cuentas:login'

# Idioma y zona horaria de Chile
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Mapa -----------------------------------------------------------------
# Django envía por defecto "Referrer-Policy: same-origin", así el navegador NO
# manda el encabezado Referer a otros sitios. Los servidores de mapas de
# OpenStreetMap exigen un Referer válido y, sin él, devuelven la imagen
# "Access blocked". Con esta política se envía solo el origen
# (ej: http://nexu.localhost:8000), nunca la ruta completa.
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Proveedor de mapas (ambos gratis y sin API key):
#   'osm'   -> OpenStreetMap (por defecto)
#   'carto' -> CARTO Voyager (mismos datos de OpenStreetMap, otro servidor).
#              Úsalo si en tu red OpenStreetMap sigue bloqueando los mapas.
MAPA_PROVEEDOR = 'osm'

# --- Telegram -------------------------------------------------------------
# El token se lee desde nexu/config_local.py (excluido de git). Si el archivo
# no existe, la app funciona igual y la opción de Telegram queda deshabilitada.
try:
    from .config_local import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME
except ImportError:
    TELEGRAM_BOT_TOKEN = ''
    TELEGRAM_BOT_USERNAME = ''

# Segundos máximos de espera al llamar a la API de Telegram.
TELEGRAM_TIMEOUT = 8
