"""Configuração de execução do backend. Todos os valores vêm do ambiente (ver `config/env.py`)."""

import os

from django.core.exceptions import ImproperlyConfigured

from config import env
from config.logging_config import build_logging, log_startup_failure, resolve_log_dir
from config.storage import build_storages

try:
    _required = env.require_env(env.REQUIRED_VARS)
except ImproperlyConfigured as error:
    log_startup_failure(error)
    raise

SECRET_KEY = _required["DJANGO_SECRET_KEY"]
DEBUG = env.get_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env.get_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

# Proteções do modo restritivo (depuração desligada). Em HTTP local com DEBUG=False,
# defina DJANGO_HTTPS_ONLY=False, senão o login do painel não persiste (cookie seguro).
HTTPS_ONLY = env.get_bool("DJANGO_HTTPS_ONLY", not DEBUG)
SECURE_SSL_REDIRECT = HTTPS_ONLY
SESSION_COOKIE_SECURE = HTTPS_ONLY
CSRF_COOKIE_SECURE = HTTPS_ONLY
SECURE_HSTS_SECONDS = 3600 if HTTPS_ONLY else 0
# Valem em qualquer modo.
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SECURE_REFERRER_POLICY = "same-origin"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.core",
    "apps.units",
    "apps.categories",
    "apps.activities",
    "apps.schedules",
    "apps.audiences",
    "apps.consultation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
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

# Imagens das atividades no Amazon S3 (o banco guarda só o nome do objeto).
STORAGES = build_storages(_required)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "apps.core.exceptions.public_exception_handler",
}

# Origens do frontend (repositório separado). Vazio = nenhuma origem autorizada.
CORS_ALLOWED_ORIGINS = env.get_list("CORS_ALLOWED_ORIGINS")

# Registro de erros em arquivo local, com rotação e sem segredos (ver `config/logging_config.py`).
LOGGING = build_logging(
    resolve_log_dir(),
    env.get_log_level(),
    env.get_int("LOG_MAX_BYTES", 1048576, 1),
    env.get_int("LOG_BACKUP_COUNT", 5, 0),
    (SECRET_KEY, _required["DB_PASSWORD"], _required["AWS_SECRET_ACCESS_KEY"]),
)
