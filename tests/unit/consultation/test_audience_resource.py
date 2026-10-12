import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.consultation import views
from apps.consultation.serializers import AudienceItemSerializer

client = APIClient()
FORBIDDEN = ("is_active", "includes_everyone", "created_at", "updated_at", "created_by")


def _audience(name, description="", **extra):
    values = {
        "id": uuid.uuid4(),
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "description": description,
        "is_active": True,
        "includes_everyone": False,
    }
    values.update(extra)
    return SimpleNamespace(**values)


@pytest.fixture
def source():
    with patch.object(views, "TargetAudience") as model:
        yield model.objects


def _serve(source, items):
    source.filter.return_value.order_by.return_value = items
    return client.get("/api/v1/audiences/")


def test_item_has_exactly_the_public_fields():
    data = AudienceItemSerializer(_audience("Adultos", "Maiores de 18 anos")).data

    assert dict(data) == {
        "id": data["id"],
        "name": "Adultos",
        "slug": "adultos",
        "description": "Maiores de 18 anos",
    }
    assert list(data) == ["id", "name", "slug", "description"]


def test_empty_description_is_null():
    assert AudienceItemSerializer(_audience("Adultos", "")).data["description"] is None


def test_list_uses_the_paginated_envelope(source):
    response = _serve(source, [_audience("Adultos"), _audience("Crianças")])

    body = response.json()
    assert response.status_code == 200
    assert set(body) == {"count", "next", "previous", "results"}
    assert body["count"] == 2 and [item["name"] for item in body["results"]] == [
        "Adultos",
        "Crianças",
    ]


def test_only_active_audiences_are_asked_for_and_sorted_by_name(source):
    _serve(source, [])

    source.filter.assert_called_once_with(is_active=True)
    source.filter.return_value.order_by.assert_called_once_with("name")


def test_no_audiences_is_an_empty_list(source):
    body = _serve(source, []).json()

    assert body == {"count": 0, "next": None, "previous": None, "results": []}


def test_pagination_follows_the_other_support_lists(source):
    items = [_audience(f"Público {n:02d}") for n in range(5)]

    body = _serve(source, items)
    paged = client.get("/api/v1/audiences/?page=2&page_size=2").json()

    assert body.json()["count"] == 5
    assert len(paged["results"]) == 2 and paged["previous"] and paged["next"]


def test_invalid_page_is_a_400_on_the_page_field(source):
    source.filter.return_value.order_by.return_value = [_audience("Adultos")]

    response = client.get("/api/v1/audiences/?page=99")

    assert response.status_code == 400
    assert response.json()["errors"] == {"page": ["Informe uma página válida."]}


def test_response_has_no_administrative_data(source):
    text = _serve(source, [_audience("Todas as idades", includes_everyone=True)]).content.decode()

    assert not any(name in text for name in FORBIDDEN)


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_writes_are_refused(method):
    response = getattr(client, method)("/api/v1/audiences/")

    assert response.status_code == 405
    assert response.json() == {"detail": "Método não permitido."}


def test_there_is_no_detail_route():
    assert client.get(f"/api/v1/audiences/{uuid.uuid4()}/").status_code == 404


def test_invalid_credentials_are_ignored(source):
    source.filter.return_value.order_by.return_value = []

    response = client.get("/api/v1/audiences/", HTTP_AUTHORIZATION="Basic invalido")

    assert response.status_code == 200
