import logging
import logging.config
from types import SimpleNamespace

import pytest
from rest_framework.exceptions import MethodNotAllowed, NotFound, PermissionDenied, ValidationError

from apps.core.exceptions import UNEXPECTED_ERROR_MESSAGE, public_exception_handler
from config.logging_config import LOG_FILE_NAME, build_logging

PASSWORD = "senha-do-banco-456"
SECRETS = ("chave-secreta-de-teste-123", PASSWORD)


@pytest.fixture
def log_file(tmp_path):
    logging.config.dictConfig(build_logging(tmp_path, "ERROR", 100000, 1, SECRETS))
    yield tmp_path / LOG_FILE_NAME
    for name in ("apps", "config", "django.request"):
        logger = logging.getLogger(name)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


def _request():
    return SimpleNamespace(
        method="GET",
        path="/api/v1/activities/",
        GET={"q": "busca-privada"},
        headers={"Authorization": "Bearer abc", "Cookie": "sessionid=xyz"},
        META={"HTTP_COOKIE": "sessionid=xyz"},
        body=b"corpo-privado",
    )


def _flush():
    for handler in logging.getLogger("apps").handlers:
        handler.flush()


def test_unexpected_error_is_logged_with_method_path_and_type(log_file):
    response = public_exception_handler(RuntimeError("quebrou"), {"request": _request()})
    _flush()

    text = log_file.read_text(encoding="utf-8")
    assert "ERROR apps.core.exceptions" in text
    assert "GET /api/v1/activities/" in text
    assert "RuntimeError: quebrou" in text
    for private in ("busca-privada", "Bearer abc", "sessionid=xyz", "corpo-privado"):
        assert private not in text
    assert response.status_code == 500
    assert response.data == {"detail": UNEXPECTED_ERROR_MESSAGE}


def test_secret_in_exception_message_is_masked(log_file):
    public_exception_handler(
        RuntimeError(f"falha ao conectar password={PASSWORD}"), {"request": _request()}
    )
    _flush()

    assert PASSWORD not in log_file.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "error",
    [
        ValidationError({"page": ["inválida"]}),
        NotFound(),
        MethodNotAllowed("POST"),
        PermissionDenied(),
    ],
)
def test_expected_client_errors_are_not_logged(log_file, error):
    public_exception_handler(error, {"request": _request()})
    _flush()

    assert not log_file.exists() or log_file.read_text(encoding="utf-8") == ""
