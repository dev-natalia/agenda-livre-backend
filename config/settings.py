"""Configuração de execução do backend. Todos os valores vêm do ambiente (ver `config/env.py`)."""

import os

from config import env

_required = env.require_env(env.REQUIRED_VARS)

SECRET_KEY = _required["DJANGO_SECRET_KEY"]
DEBUG = env.get_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env.get_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "corsheaders",
    "rest_framework",
    "apps.core",
    "apps.units",
    "apps.categories",
    "apps.activities",
    "apps.schedules",
    "apps.audiences",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

_db_options = {
    "sslmode": env.get_ssl_mode(),
    "connect_timeout": 15,
}
if os.environ.get("DB_SSLROOTCERT", "").strip():
    _db_options["sslrootcert"] = os.environ["DB_SSLROOTCERT"].strip()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": _required["DB_HOST"],
        "PORT": env.parse_port(_required["DB_PORT"]),
        "NAME": _required["DB_NAME"],
        "USER": _required["DB_USER"],
        "PASSWORD": _required["DB_PASSWORD"],
        "OPTIONS": _db_options,
    }
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# Origens do frontend (repositório separado). Vazio = nenhuma origem autorizada.
CORS_ALLOWED_ORIGINS = env.get_list("CORS_ALLOWED_ORIGINS")
