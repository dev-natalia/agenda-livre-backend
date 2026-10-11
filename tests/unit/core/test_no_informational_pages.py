"""Sobre e Contato existem só no frontend: o backend não tem rota, modelo nem cadastro para eles."""

import json
import re
from unittest.mock import PropertyMock, patch

import pytest
from django.apps import apps
from django.contrib import admin
from django.test import Client, RequestFactory
from django.urls import URLPattern, URLResolver, get_resolver

from apps.core import error_views

FORBIDDEN_WORDS = re.compile(r"contact|contato|about|sobre|message", re.IGNORECASE)
ALLOWED_NAMES: set[str] = set()
SENTINEL = "sentinela-contato-123"
NOT_FOUND = {"detail": "Não encontrado."}
PATHS = [
    "/api/contact/",
    "/api/contato/",
    "/api/v1/contact/",
    "/api/v1/contato/",
    "/api/about/",
    "/api/sobre/",
    "/api/v1/about/",
    "/api/v1/sobre/",
]


def _route_patterns(patterns=None, prefix=""):
    patterns = get_resolver().url_patterns if patterns is None else patterns
    for entry in patterns:
        text = prefix + str(entry.pattern)
        if isinstance(entry, URLResolver):
            yield from _route_patterns(entry.url_patterns, text)
        elif isinstance(entry, URLPattern):
            yield text


def test_route_scan_sees_the_known_routes():
    routes = list(_route_patterns())
    for expected in ("activities", "units", "categories"):
        assert any(expected in route for route in routes)


def test_no_route_handles_contact_or_about():
    routes = _route_patterns()
    offenders = [r for r in routes if FORBIDDEN_WORDS.search(r) and r not in ALLOWED_NAMES]
    assert offenders == []


def test_model_scan_sees_the_known_models():
    assert "Activity" in {model.__name__ for model in apps.get_models()}


def test_no_model_stores_contact_or_about_content():
    names = {model.__name__ for model in apps.get_models()}
    assert [n for n in names if FORBIDDEN_WORDS.search(n) and n not in ALLOWED_NAMES] == []


def test_admin_scan_sees_the_known_models():
    assert "Activity" in {model.__name__ for model in admin.site._registry}


def test_no_admin_registration_for_contact_or_about():
    names = {model.__name__ for model in admin.site._registry}
    assert [n for n in names if FORBIDDEN_WORDS.search(n) and n not in ALLOWED_NAMES] == []


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
@pytest.mark.parametrize("path", PATHS)
def test_informational_paths_are_json_not_found_even_with_csrf_checks(method, path):
    client = Client(enforce_csrf_checks=True)
    response = getattr(client, method)(path, HTTP_HOST="localhost")
    assert response.status_code == 404
    assert response["Content-Type"] == "application/json"
    assert response.json() == NOT_FOUND


def test_contact_post_body_is_neither_read_nor_logged(caplog):
    request = RequestFactory().post("/api/contato/", {"mensagem": SENTINEL})
    with (
        caplog.at_level("DEBUG"),
        patch.object(type(request), "body", new_callable=PropertyMock) as body,
    ):
        response = error_views.api_not_found(request)
    body.assert_not_called()
    assert response.status_code == 404
    assert json.loads(response.content) == NOT_FOUND
    assert SENTINEL not in response.content.decode()
    assert SENTINEL not in caplog.text


def test_contact_post_through_client_leaves_no_trace_in_logs(caplog):
    with caplog.at_level("DEBUG"):
        Client(enforce_csrf_checks=True).post(
            "/api/contato/", {"mensagem": SENTINEL}, HTTP_HOST="localhost"
        )
    assert SENTINEL not in caplog.text
