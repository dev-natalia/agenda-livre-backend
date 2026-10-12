import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from consultation_helpers import activity, manager, occurrence
from rest_framework.test import APIClient

from apps.consultation import services, views

client = APIClient()


def _audience(name, includes_everyone=False):
    pk = uuid.uuid4()
    return SimpleNamespace(pk=pk, id=pk, name=name, includes_everyone=includes_everyone)


ADULTS = _audience("Adultos")
CHILDREN = _audience("Crianças")
EVERYONE = _audience("Todas as idades", includes_everyone=True)


def _item(title, *audiences):
    return activity(title, target_audiences=manager(audiences))


@pytest.fixture
def catalog():
    items = [
        _item("Para adultos", ADULTS),
        _item("Para crianças", CHILDREN),
        _item("Para todos", EVERYONE),
        _item("Adultos e todos", ADULTS, EVERYONE),
        _item("Sem público"),
    ]
    with (
        patch.object(views, "published_activities", return_value=items) as source,
        patch("apps.consultation.services.activity_occurrences") as calc,
        patch.object(services, "find_audience") as find,
    ):
        calc.return_value = [occurrence(date(2026, 11, 20))]
        find.side_effect = lambda pk: {a.pk: a for a in (ADULTS, CHILDREN, EVERYONE)}.get(pk)
        source.find = find
        yield source


def _titles(response):
    return [found["title"] for found in response.json()["results"]]


def test_filtering_by_a_specific_audience_includes_everyone(catalog):
    response = client.get(f"/api/v1/activities/?audience={ADULTS.pk}")

    assert response.status_code == 200
    assert _titles(response) == ["Adultos e todos", "Para adultos", "Para todos"]
    assert response.json()["count"] == 3


def test_filtering_by_the_everyone_audience_returns_only_its_activities(catalog):
    response = client.get(f"/api/v1/activities/?audience={EVERYONE.pk}")

    assert _titles(response) == ["Adultos e todos", "Para todos"]


def test_activity_linked_to_two_matching_audiences_is_listed_once(catalog):
    response = client.get(f"/api/v1/activities/?audience={ADULTS.pk}")

    assert _titles(response).count("Adultos e todos") == 1
    assert response.json()["count"] == len(response.json()["results"])


def test_unknown_or_inactive_audience_is_an_empty_list(catalog):
    response = client.get(f"/api/v1/activities/?audience={uuid.uuid4()}")

    assert response.status_code == 200
    assert response.json() == {"count": 0, "next": None, "previous": None, "results": []}


def test_invalid_audience_is_a_400_on_its_field(catalog):
    response = client.get("/api/v1/activities/?audience=abc")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Parâmetros inválidos.",
        "errors": {"audience": ["Informe um identificador válido."]},
    }
    catalog.find.assert_not_called()


def test_empty_audience_is_ignored_like_an_empty_unit_or_category(catalog):
    response = client.get("/api/v1/activities/?audience=")

    assert response.status_code == 200
    assert response.json()["count"] == 5
    catalog.find.assert_not_called()


def test_without_audience_the_list_is_unchanged_and_no_lookup_is_made(catalog):
    response = client.get("/api/v1/activities/")

    assert response.json()["count"] == 5
    assert _titles(response) == [
        "Adultos e todos", "Para adultos", "Para crianças", "Para todos", "Sem público",
    ]  # fmt: skip
    catalog.find.assert_not_called()


def test_only_published_activities_are_read(catalog):
    client.get(f"/api/v1/activities/?audience={ADULTS.pk}")

    catalog.assert_called_once()


def test_writes_are_still_refused():
    assert client.post(f"/api/v1/activities/?audience={ADULTS.pk}").status_code == 405


def test_pagination_counts_distinct_activities(catalog):
    body = client.get(f"/api/v1/activities/?audience={ADULTS.pk}&page_size=2").json()

    assert body["count"] == 3
    assert len(body["results"]) == 2 and body["next"] and body["previous"] is None
