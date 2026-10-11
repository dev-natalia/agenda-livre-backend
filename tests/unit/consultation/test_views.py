import uuid
from datetime import date
from unittest.mock import patch

import pytest
from consultation_helpers import activity, category, occurrence, one_time, unit
from django.test import override_settings
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory

from apps.consultation import views
from apps.consultation.views import PublicAPIView

FORBIDDEN = ("created_by", "updated_by", "created_at", "updated_at", "status", "is_active")
client = APIClient()


class _Probe(PublicAPIView):
    def get(self, request):
        return Response({"ok": True})


@pytest.fixture
def catalog():
    """Atividades em memória servidas no lugar da consulta ao banco."""
    items = []
    with (
        patch.object(views, "published_activities", return_value=items) as source,
        patch("apps.consultation.services.activity_occurrences") as calc,
    ):
        calc.return_value = [occurrence(date(2026, 11, 20))]
        source.items = items
        source.calc = calc
        yield source


def _get(url):
    return client.get(url)


# --- base ----------------------------------------------------------------


def test_write_methods_are_rejected():
    factory = APIRequestFactory()
    view = _Probe.as_view()
    for method in ("post", "put", "patch", "delete"):
        response = view(getattr(factory, method)("/x/"))
        assert response.status_code == 405
        assert response.data == {"detail": "Método não permitido."}


def test_invalid_credentials_are_ignored():
    request = APIRequestFactory().get("/x/", HTTP_AUTHORIZATION="Basic invalido")
    assert _Probe.as_view()(request).status_code == 200


# --- listagem ------------------------------------------------------------


def test_list_is_anonymous_and_paginated(catalog):
    catalog.items.extend(activity(f"Atividade {n:02d}") for n in range(30))
    response = _get("/api/v1/activities/")
    body = response.json()
    assert response.status_code == 200
    assert body["count"] == 30 and len(body["results"]) == 12
    assert body["next"] and body["previous"] is None


def test_list_page_size_and_page(catalog):
    catalog.items.extend(activity(f"Atividade {n:02d}") for n in range(5))
    body = _get("/api/v1/activities/?page=2&page_size=2").json()
    assert len(body["results"]) == 2 and body["previous"] and body["next"]
    assert len(_get("/api/v1/activities/?page_size=500").json()["results"]) == 5


@pytest.mark.parametrize("page", ["99", "abc"])
def test_list_invalid_page_is_json_400_on_page_field(catalog, page):
    response = _get(f"/api/v1/activities/?page={page}")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Parâmetros inválidos.",
        "errors": {"page": ["Informe uma página válida."]},
    }


def test_empty_list(catalog):
    response = _get("/api/v1/activities/")
    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_list_item_shape_and_no_leaks(catalog):
    catalog.items.append(activity("Oficina de dança"))
    text = _get("/api/v1/activities/").content.decode()
    assert '"next_occurrence":{"date":"2026-11-20","start_time":"14:00","end_time":"15:00"}' in text
    assert not any(name in text for name in FORBIDDEN)


def test_list_rejects_writes():
    for method in (client.post, client.put, client.patch, client.delete):
        response = method("/api/v1/activities/")
        assert response.status_code == 405
        assert response.json() == {"detail": "Método não permitido."}


def test_list_ignores_invalid_credentials(catalog):
    catalog.items.append(activity("A"))
    response = client.get("/api/v1/activities/", HTTP_AUTHORIZATION="Basic invalido")
    assert response.status_code == 200 and response.json()["count"] == 1


# --- busca e filtros -----------------------------------------------------


def test_search_filters_with_accents_and_case(catalog):
    catalog.items.extend([activity("Oficina de dança"), activity("Xadrez")])
    body = _get("/api/v1/activities/?q=DANCA").json()
    assert [item["title"] for item in body["results"]] == ["Oficina de dança"]
    assert _get("/api/v1/activities/?q=nada-disso").json()["count"] == 0


@pytest.mark.parametrize("query", ["q=", "q=%20%20", "foo=1"])
def test_blank_search_and_unknown_params_return_everything(catalog, query):
    catalog.items.extend([activity("A"), activity("B")])
    assert _get(f"/api/v1/activities/?{query}").json()["count"] == 2


def test_search_too_long_is_400(catalog):
    response = _get("/api/v1/activities/?q=" + "a" * 101)
    assert response.status_code == 400
    assert response.json()["detail"] == "Parâmetros inválidos."
    assert "q" in response.json()["errors"]


def test_unit_and_category_filters_reach_the_query(catalog):
    wanted_unit, wanted_category = uuid.uuid4(), uuid.uuid4()
    _get(f"/api/v1/activities/?unit={wanted_unit}&category={wanted_category}")
    criteria = catalog.call_args.args[0]
    assert criteria.unit == wanted_unit and criteria.category == wanted_category


@pytest.mark.parametrize("name", ["unit", "category"])
def test_malformed_ids_are_400(catalog, name):
    response = _get(f"/api/v1/activities/?{name}=abc")
    assert response.status_code == 400 and name in response.json()["errors"]


def test_neighborhood_filter(catalog):
    catalog.items.extend(
        [
            activity("A", unit=unit(neighborhood="Grajaú")),
            activity("B", unit=unit(neighborhood="X")),
        ]
    )
    body = _get("/api/v1/activities/?neighborhood=grajau").json()
    assert [item["title"] for item in body["results"]] == ["A"]


def test_date_filter_reaches_the_calculation(catalog):
    catalog.items.append(activity("A"))
    _get("/api/v1/activities/?date=2026-11-20")
    kwargs = catalog.calc.call_args.kwargs
    assert kwargs["date_from"] == kwargs["date_to"] == date(2026, 11, 20)
    _get("/api/v1/activities/?date_from=2026-11-01&date_to=2026-11-30")
    kwargs = catalog.calc.call_args.kwargs
    assert (kwargs["date_from"], kwargs["date_to"]) == (date(2026, 11, 1), date(2026, 11, 30))
    _get("/api/v1/activities/?date_from=2026-11-01")
    kwargs = catalog.calc.call_args.kwargs
    assert (kwargs["date_from"], kwargs["date_to"]) == (date(2026, 11, 1), None)


def test_date_filter_drops_activities_without_occurrence(catalog):
    catalog.items.append(activity("A"))
    catalog.calc.return_value = []
    assert _get("/api/v1/activities/?date=2026-11-20").json()["count"] == 0
    assert _get("/api/v1/activities/").json()["count"] == 1


@pytest.mark.parametrize(
    "query",
    [
        "date_from=2026-12-31&date_to=2026-12-01",
        "date=2026-12-01&date_to=2026-12-05",
        "date_from=2026-01-01&date_to=2027-12-31",
        "date=20/11/2026",
    ],
)
def test_invalid_dates_are_400_without_calculation(catalog, query):
    response = _get(f"/api/v1/activities/?{query}")
    assert response.status_code == 400
    assert not catalog.calc.called


def test_combined_filters_are_consistent_across_pages(catalog):
    catalog.items.extend(activity(f"Dança {n:02d}") for n in range(15))
    base = "/api/v1/activities/?q=danca&date_from=2026-11-01&date_to=2026-11-30&page_size=10"
    first, second = _get(base).json(), _get(base + "&page=2").json()
    assert first["count"] == second["count"] == 15
    titles = [item["title"] for item in first["results"] + second["results"]]
    assert titles == sorted(titles)


# --- detalhe -------------------------------------------------------------


@pytest.fixture
def detail_source():
    with (
        patch.object(views, "published_activities") as source,
        patch("apps.consultation.serializers.activity_occurrences", return_value=[]),
    ):
        yield source.return_value.prefetch_related.return_value.filter.return_value


def test_detail_of_published_activity(detail_source):
    item = activity("Oficina", [one_time(date(2026, 11, 20))])
    detail_source.first.return_value = item
    response = _get(f"/api/v1/activities/{item.id}/")
    body = response.json()
    assert response.status_code == 200
    assert body["title"] == "Oficina" and len(body["schedules"]) == 1
    assert not any(name in response.content.decode() for name in FORBIDDEN)


@pytest.mark.parametrize("key", ["abc", "123", str(uuid.uuid4())])
def test_detail_not_found_is_uniform(detail_source, key):
    detail_source.first.return_value = None
    response = _get(f"/api/v1/activities/{key}/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Não encontrado."}


def test_detail_only_queries_published_activities():
    with patch.object(views, "published_activities") as source:
        chain = source.return_value.prefetch_related.return_value.filter.return_value
        chain.first.return_value = None
        _get(f"/api/v1/activities/{uuid.uuid4()}/")
    source.assert_called_once_with()


def test_detail_rejects_writes():
    assert client.post(f"/api/v1/activities/{uuid.uuid4()}/").status_code == 405


# --- unidades e categorias -----------------------------------------------


def test_unit_list_only_active_sorted_by_name():
    units = [unit("A", address="", description="")]
    with patch.object(views, "Unit") as model:
        model.objects.filter.return_value.order_by.return_value = units
        response = _get("/api/v1/units/")
    model.objects.filter.assert_called_once_with(is_active=True)
    model.objects.filter.return_value.order_by.assert_called_once_with("name")
    body = response.json()
    assert body["count"] == 1 and body["results"][0]["address"] is None
    assert not any(name in response.content.decode() for name in FORBIDDEN)


def test_category_list_only_active_sorted_by_name():
    with patch.object(views, "Category") as model:
        model.objects.filter.return_value.order_by.return_value = [category("Esporte")]
        response = _get("/api/v1/categories/")
    model.objects.filter.assert_called_once_with(is_active=True)
    model.objects.filter.return_value.order_by.assert_called_once_with("name")
    assert response.json()["results"][0]["name"] == "Esporte"


def test_empty_lists():
    with patch.object(views, "Unit") as model:
        model.objects.filter.return_value.order_by.return_value = []
        assert _get("/api/v1/units/").json()["count"] == 0


def test_support_lists_reject_writes_and_have_no_detail_route():
    assert client.post("/api/v1/units/").status_code == 405
    assert client.delete("/api/v1/categories/").status_code == 405
    assert _get(f"/api/v1/units/{uuid.uuid4()}/").status_code == 404
    assert _get(f"/api/v1/categories/{uuid.uuid4()}/").status_code == 404


# --- CORS ----------------------------------------------------------------


@override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:5500"])
def test_cors_header_for_authorized_origin(catalog):
    allowed = client.get("/api/v1/activities/", HTTP_ORIGIN="http://localhost:5500")
    other = client.get("/api/v1/activities/", HTTP_ORIGIN="http://outro.exemplo")
    assert allowed["Access-Control-Allow-Origin"] == "http://localhost:5500"
    assert "Access-Control-Allow-Origin" not in other
