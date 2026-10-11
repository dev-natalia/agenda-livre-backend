"""Registro de erros em arquivo local, com rotação e sem segredos.

Nenhuma função deste módulo levanta exceção por falha de gravação: o registro de erros nunca pode
derrubar a aplicação nem alterar a resposta enviada ao visitante.
"""

import logging
import logging.handlers
import os
import re
import sys
from pathlib import Path

from config.env import BASE_DIR

LOG_FILE_NAME = "agenda-livre.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
LOGGER_NAMES = ("apps", "config", "django.request")
MASK = "***"
MIN_SECRET_LENGTH = 4

_SECRET_WORDS = "password|passwd|pwd|secret|token|api_key|sessionid|csrftoken"
_LINE_WORDS = "authorization|set-cookie|cookie"
_URL_CREDENTIALS = re.compile(r"(\w+://[^\s:/@]+:)[^\s@/]+(@)")
_LINE_PAIR = re.compile(
    rf"([\w-]*(?:{_LINE_WORDS})[\w-]*\s*[=:]\s*)[^\r\n]*", re.IGNORECASE
)
_VALUE_PAIR = re.compile(
    rf"([\w-]*(?:{_SECRET_WORDS})[\w-]*\s*[=:]\s*)[^\s,;&'\"]+", re.IGNORECASE
)


class RedactingFormatter(logging.Formatter):
    """Formata o registro inteiro (mensagem e rastreamento) e só então mascara os segredos."""

    def __init__(self, fmt=LOG_FORMAT, datefmt=None, secrets=()):
        super().__init__(fmt, datefmt)
        self._secrets = tuple(
            secret for secret in secrets if secret and len(secret) >= MIN_SECRET_LENGTH
        )

    def format(self, record):
        return self._mask(super().format(record))

    def _mask(self, text):
        for secret in self._secrets:
            text = text.replace(secret, MASK)
        text = _URL_CREDENTIALS.sub(rf"\1{MASK}\2", text)
        text = _LINE_PAIR.sub(rf"\1{MASK}", text)
        return _VALUE_PAIR.sub(rf"\1{MASK}", text)


def resolve_log_dir(raw=None):
    """Pasta dos registros: `LOG_DIR` (relativa à raiz do repositório) ou `logs`."""
    value = raw if raw is not None else os.environ.get("LOG_DIR", "")
    path = Path(value.strip() or "logs")
    return path if path.is_absolute() else BASE_DIR / path


def build_logging(log_dir, level, max_bytes, backup_count, secrets):
    """Monta o dicionário `LOGGING`. Sem permissão para a pasta, usa só o console."""
    formatters = {
        "redacting": {
            "()": "config.logging_config.RedactingFormatter",
            "fmt": LOG_FORMAT,
            "secrets": tuple(secrets),
        }
    }
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": "redacting",
        }
    }
    handler_names = ["console"]
    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        print(
            "Aviso: registro de erros em arquivo desativado (sem acesso à pasta de logs).",
            file=sys.stderr,
        )
    else:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "redacting",
            "filename": str(Path(log_dir) / LOG_FILE_NAME),
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "delay": True,
            "encoding": "utf-8",
        }
        handler_names.append("file")
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": {
            name: {"handlers": list(handler_names), "level": level} for name in LOGGER_NAMES
        },
    }


def log_startup_failure(error):
    """Grava uma falha de inicialização antes de o Django montar o `LOGGING`. Nunca levanta."""
    handler = None
    try:
        log_dir = resolve_log_dir()
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            Path(log_dir) / LOG_FILE_NAME, maxBytes=1048576, backupCount=5, encoding="utf-8"
        )
        secrets = (os.environ.get("DJANGO_SECRET_KEY", ""), os.environ.get("DB_PASSWORD", ""))
        handler.setFormatter(RedactingFormatter(secrets=secrets))
        logger = logging.getLogger("config.startup")
        record = logger.makeRecord(
            logger.name, logging.ERROR, __file__, 0, "Falha de inicialização: %s", (error,), None
        )
        handler.handle(record)
    except Exception:  # noqa: BLE001 - registrar falha nunca pode impedir o erro original
        pass
    finally:
        if handler is not None:
            handler.close()
