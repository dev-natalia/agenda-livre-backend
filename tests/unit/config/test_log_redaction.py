import logging
import sys

import pytest

from config.logging_config import RedactingFormatter

SECRET_KEY = "chave-secreta-de-teste-123"
DB_PASSWORD = "senha-do-banco-456"


def _format(message, *, secrets=(SECRET_KEY, DB_PASSWORD), exc_info=None):
    record = logging.LogRecord("apps.x", logging.ERROR, __file__, 1, message, None, exc_info)
    return RedactingFormatter("%(levelname)s %(name)s: %(message)s", secrets=secrets).format(record)


def test_masks_real_secret_values():
    text = _format(f"falha com {SECRET_KEY} e {DB_PASSWORD}")

    assert SECRET_KEY not in text
    assert DB_PASSWORD not in text
    assert text.count("***") == 2


def test_ignores_empty_and_short_secrets():
    text = _format("erro comum com abc", secrets=("", "abc", None))

    assert text == "ERROR apps.x: erro comum com abc"


@pytest.mark.parametrize(
    "name",
    [
        "password", "passwd", "pwd", "secret", "token", "api_key", "authorization",
        "cookie", "set-cookie", "sessionid", "csrftoken",
    ],
)
@pytest.mark.parametrize("separator", ["=", ": ", " = "])
def test_masks_key_value_pairs(name, separator):
    text = _format(f"dados {name.upper()}{separator}valorsensivel fim")

    assert "valorsensivel" not in text
    assert "***" in text


def test_masks_credentials_in_urls():
    text = _format("conectando em postgres://admin:umasenha@db.exemplo.local:5432/agenda")

    assert "umasenha" not in text
    assert "postgres://admin:***@db.exemplo.local:5432/agenda" in text


def test_masks_secret_inside_traceback():
    try:
        raise RuntimeError(f"erro de conexao password={DB_PASSWORD} host=x")
    except RuntimeError:
        text = _format("falha inesperada", exc_info=sys.exc_info())

    assert "RuntimeError" in text
    assert "Traceback" in text
    assert DB_PASSWORD not in text


def test_keeps_non_sensitive_text():
    text = _format("Erro inesperado em GET /api/v1/activities/")

    assert text == "ERROR apps.x: Erro inesperado em GET /api/v1/activities/"
