from types import SimpleNamespace
from unittest.mock import patch

from django.http import Http404
from rest_framework.exceptions import (
    MethodNotAllowed,
    NotFound,
    PermissionDenied,
    ValidationError,
)

from apps.core.exceptions import public_exception_handler


def _handle(exc):
    return public_exception_handler(exc, {"view": None, "request": None})


def test_validation_error_with_field_dict():
    response = _handle(ValidationError({"q": ["Muito longo."], "unit": "Inválido."}))
    assert response.status_code == 400
    assert response.data == {
        "detail": "Parâmetros inválidos.",
        "errors": {"q": ["Muito longo."], "unit": ["Inválido."]},
    }


def test_validation_error_with_list_and_text():
    assert _handle(ValidationError(["a", "b"])).data["errors"] == {"non_field_errors": ["a", "b"]}
    assert _handle(ValidationError("a")).data["errors"] == {"non_field_errors": ["a"]}


def test_not_found_hides_original_text():
    for exc in (NotFound("atividade 123 em rascunho"), Http404("segredo")):
        response = _handle(exc)
        assert response.status_code == 404
        assert response.data == {"detail": "Não encontrado."}


def test_method_not_allowed():
    response = _handle(MethodNotAllowed("POST"))
    assert response.status_code == 405
    assert response.data == {"detail": "Método não permitido."}


def test_other_api_errors_keep_detail_text_without_errors_key():
    response = _handle(PermissionDenied("Sem permissão."))
    assert response.data == {"detail": "Sem permissão."}


def test_unexpected_exception_gets_generic_500_without_original_text():
    response = _handle(RuntimeError("senha=abc123 em /srv/app/arquivo.py"))
    assert response.status_code == 500
    assert response.data == {"detail": "Ocorreu um erro inesperado. Tente novamente mais tarde."}


def test_unexpected_exception_is_logged_with_method_and_path_only(caplog):
    request = SimpleNamespace(method="GET", path="/api/v1/activities/", body=b"segredo")
    with caplog.at_level("ERROR", logger="apps.core.exceptions"):
        public_exception_handler(RuntimeError("boom"), {"request": request})
    assert len(caplog.records) == 1
    assert caplog.records[0].getMessage() == "Erro inesperado em GET /api/v1/activities/"
    assert "segredo" not in caplog.text
    assert caplog.records[0].exc_info[0] is RuntimeError


def test_exception_without_detail_attribute_uses_text():
    with patch("apps.core.exceptions.exception_handler") as base:
        base.return_value = type("R", (), {"data": None})()
        response = _handle(RuntimeError("falha"))
    assert response.data == {"detail": "falha"}


def test_body_never_contains_traceback():
    assert "Traceback" not in str(_handle(ValidationError({"q": ["x"]})).data)
