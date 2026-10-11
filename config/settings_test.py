"""Configuração dos testes: sem variáveis reais e sem nenhum acesso a banco de dados."""

import os
import tempfile

_FAKE_ENV = {
    "DJANGO_SECRET_KEY": "test-secret-key-not-for-production",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "test",
    "DB_USER": "test",
    "DB_PASSWORD": "test",
}
for _name, _value in _FAKE_ENV.items():
    os.environ.setdefault(_name, _value)

# Registros de teste nunca vão para `logs/` do repositório.
# O cliente de teste usa HTTP; as proteções de HTTPS são verificadas em test_security_settings.
os.environ.setdefault("DJANGO_HTTPS_ONLY", "False")
os.environ["LOG_DIR"] = tempfile.mkdtemp(prefix="agenda-livre-logs-")

from config.settings import *  # noqa: E402, F401, F403

DATABASES = {"default": {"ENGINE": "config.blocked_db"}}
