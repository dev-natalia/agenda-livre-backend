"""Leitura e validação das variáveis de ambiente.

Nenhuma função deste módulo imprime ou inclui valores de variáveis em mensagens de erro.
"""

import os
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

REQUIRED_VARS = (
    "DJANGO_SECRET_KEY",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_STORAGE_BUCKET_NAME",
    "AWS_S3_REGION_NAME",
)

OPTIONAL_VARS = (
    "DJANGO_DEBUG",
    "DJANGO_ALLOWED_HOSTS",
    "DB_SSLMODE",
    "DB_SSLROOTCERT",
    "CORS_ALLOWED_ORIGINS",
    "DJANGO_HTTPS_ONLY",
    "LOG_DIR",
    "LOG_LEVEL",
    "LOG_MAX_BYTES",
    "LOG_BACKUP_COUNT",
)

ALL_VARS = REQUIRED_VARS + OPTIONAL_VARS

SSL_MODES = ("disable", "allow", "prefer", "require", "verify-ca", "verify-full")

LOG_LEVELS = ("WARNING", "ERROR", "CRITICAL")

_TRUE_VALUES = ("true", "1", "yes")
_FALSE_VALUES = ("false", "0", "no")


def load_dotenv():
    """Carrega o arquivo `.env` da raiz do repositório, se existir.

    Variáveis já definidas no ambiente do processo têm precedência.
    """
    environ.Env.read_env(BASE_DIR / ".env")


def require_env(names):
    """Devolve as variáveis obrigatórias ou levanta erro listando todas as ausentes."""
    missing = [name for name in names if not os.environ.get(name, "").strip()]
    if missing:
        raise ImproperlyConfigured(
            "Configuração incompleta. Defina as variáveis de ambiente: " + ", ".join(missing)
        )
    return {name: os.environ[name].strip() for name in names}


def parse_port(value):
    """Converte `DB_PORT` em inteiro entre 1 e 65535."""
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ImproperlyConfigured("DB_PORT deve ser um número inteiro.") from None
    if not 1 <= port <= 65535:
        raise ImproperlyConfigured("DB_PORT deve estar entre 1 e 65535.")
    return port


def get_bool(name, default=False):
    """Lê uma variável booleana (`True`/`False`, `1`/`0`, `yes`/`no`)."""
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    raise ImproperlyConfigured(f"{name} deve ser True ou False.")


def get_ssl_mode():
    """Lê `DB_SSLMODE`, com padrão `require`."""
    mode = os.environ.get("DB_SSLMODE", "").strip() or "require"
    if mode not in SSL_MODES:
        raise ImproperlyConfigured("DB_SSLMODE deve ser um de: " + ", ".join(SSL_MODES) + ".")
    return mode


def get_list(name, default=""):
    """Lê uma lista separada por vírgula, ignorando itens vazios."""
    raw = os.environ.get(name, "").strip() or default
    return [item.strip() for item in raw.split(",") if item.strip()]


def get_int(name, default, minimum):
    """Lê um inteiro opcional, com valor mínimo. A mensagem de erro não mostra o valor recebido."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ImproperlyConfigured(f"{name} deve ser um número inteiro.") from None
    if value < minimum:
        raise ImproperlyConfigured(f"{name} deve ser maior ou igual a {minimum}.")
    return value


def get_log_level():
    """Lê `LOG_LEVEL`, com padrão `ERROR`."""
    level = os.environ.get("LOG_LEVEL", "").strip().upper() or "ERROR"
    if level not in LOG_LEVELS:
        raise ImproperlyConfigured("LOG_LEVEL deve ser um de: " + ", ".join(LOG_LEVELS) + ".")
    return level
