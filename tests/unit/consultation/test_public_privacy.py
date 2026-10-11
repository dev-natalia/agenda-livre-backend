from datetime import date
from unittest.mock import patch

import pytest
from consultation_helpers import activity, category, occurrence, one_time, unit
from django.urls import get_resolver
from error_helpers import find_forbidden_keys
from rest_framework.exceptions import MethodNotAllowed, NotFound, ValidationError
from rest_framework.test import APIClient

from apps.consultation import serializers, views
from apps.consultation.serializers import (
    ActivityDetailSerializer,
    ActivityListItemSerializer,
    CategoryItemSerializer,
    UnitItemSerializer,
)
from apps.consultation.views import PublicAPIView
from apps.core.exceptions import public_exception_handler

client = APIClient()


def _api_routes():
    patterns = get_resolver().url_patterns
    routes = []
    for include in patterns:
        prefix = str(include.pattern)
        if prefix != "api/v1/":
            continue
        for route in include.url_patterns:
            routes.append("/api/v1/" + str(route.pattern).replace("<str:pk>", "abc"))
    return routes


def test_there_are_public_routes_to_check():
    assert len(_api_routes()) >= 5


def test_serializer_output_has_no_internal_keys():
    item = activity("Oficina", [one_time(date(2026, 11, 10))])
    with patch.object(serializers, "activity_occurrences", return_value=[]):
        detail = ActivityDetailSerializer(item).data
    listing = ActivityListItemSerializer(many=True).to_representation(
        [(item, occurrence(date(2026, 11, 10)))]
    )
    payloads = [
        detail,
        listing,
        UnitItemSerializer(unit()).data,
        CategoryItemSerializer(category()).data,
    ]
    for payload in payloads:
        assert find_forbidden_keys(payload) == set()


@pytest.mark.parametrize(
    "exc",
    [
        ValidationError({"date": ["Informe uma data no formato AAAA-MM-DD."]}),
        NotFound(),
        MethodNotAllowed("POST"),
        RuntimeError("created_by=admin password=segredo"),
    ],
)
def test_error_bodies_have_no_internal_keys_or_leaked_text(exc):
    body = public_exception_handler(exc, {"request": None}).data
    assert find_forbidden_keys(body) == set()
    assert "segredo" not in str(body) and "admin" not in str(body)


@pytest.mark.parametrize("route", _api_routes())
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_every_public_route_rejects_writes_for_anonymous_visitors(route, method):
    response = getattr(client, method)(route)
    assert response.status_code == 405
    assert response.json() == {"detail": "Método não permitido."}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_writes_are_rejected_even_when_authenticated(method):
    authenticated = APIClient()
    authenticated.force_authenticate(user=object())
    response = getattr(authenticated, method)("/api/v1/activities/")
    assert response.status_code == 405


def test_public_base_view_is_anonymous_and_read_only():
    assert PublicAPIView.authentication_classes == []
    assert [permission.__name__ for permission in PublicAPIView.permission_classes] == ["AllowAny"]
    assert PublicAPIView.http_method_names == ["get", "head", "options"]


def test_unpublished_activity_is_indistinguishable_from_missing_one():
    with patch.object(views, "published_activities") as published:
        chain = published.return_value.prefetch_related.return_value.filter.return_value
        chain.first.return_value = None
        hidden = client.get("/api/v1/activities/00000000-0000-0000-0000-000000000001/")
    missing = client.get("/api/v1/activities/nao-existe/")
    assert hidden.status_code == missing.status_code == 404
    assert hidden.json() == missing.json() == {"detail": "Não encontrado."}
