import json
from unittest.mock import patch

import pytest
from django.test import Client, RequestFactory

from apps.core import error_views
from config import urls


def _request(path):
    return RequestFactory().get(path)


def test_api_not_found_is_json():
    response = error_views.handler404(_request("/api/v1/nada/"), Exception())
    assert response.status_code == 404
    assert json.loads(response.content) == {"detail": "Não encontrado."}


def test_api_server_error_is_generic_json():
    response = error_views.handler500(_request("/api/v1/x/"))
    assert response.status_code == 500
    assert json.loads(response.content) == {
        "detail": "Ocorreu um erro inesperado. Tente novamente mais tarde."
    }


def test_outside_api_not_found_uses_django_page():
    request, exception = _request("/admin/x/"), Exception()
    with patch.object(error_views.defaults, "page_not_found", return_value="pagina") as page:
        assert error_views.handler404(request, exception) == "pagina"
    page.assert_called_once_with(request, exception)


def test_outside_api_server_error_uses_django_page():
    request = _request("/admin/x/")
    with patch.object(error_views.defaults, "server_error", return_value="pagina") as page:
        assert error_views.handler500(request) == "pagina"
    page.assert_called_once_with(request)


@pytest.mark.parametrize("name", ["handler404", "handler500"])
def test_root_urlconf_registers_handlers(name):
    assert getattr(urls, name) == f"apps.core.error_views.{name}"


@pytest.mark.parametrize("debug", [True, False])
@pytest.mark.parametrize("path", ["/api/v1/nada/", "/api/outra/", "/api/"])
def test_unknown_api_route_is_json_even_with_debug_on(settings, debug, path):
    settings.DEBUG = debug
    response = Client().get(path, HTTP_HOST="localhost")
    assert response.status_code == 404
    assert response.json() == {"detail": "Não encontrado."}
