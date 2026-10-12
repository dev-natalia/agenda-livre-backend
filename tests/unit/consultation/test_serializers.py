import uuid
from datetime import date
from unittest.mock import patch

import pytest
from consultation_helpers import (
    activity,
    category,
    manager,
    occurrence,
    one_time,
    recurring,
    unit,
)
from django.http import QueryDict

from apps.consultation import serializers
from apps.consultation.serializers import (
    ActivityDetailSerializer,
    ActivityListItemSerializer,
    CategoryItemSerializer,
    ConsultationQuerySerializer,
    UnitItemSerializer,
)

FORBIDDEN = {"created_by", "updated_by", "created_at", "updated_at", "status", "is_active"}


def _keys(data, found=None):
    found = set() if found is None else found
    if isinstance(data, dict):
        found.update(data)
        for value in data.values():
            _keys(value, found)
    elif isinstance(data, (list, tuple)):
        for value in data:
            _keys(value, found)
    return found


def _query(**params):
    query = QueryDict(mutable=True)
    query.update(params)
    return ConsultationQuerySerializer(data=query)


def _valid(**params):
    serializer = _query(**params)
    assert serializer.is_valid(), serializer.errors
    return serializer.criteria()


def _errors(**params):
    serializer = _query(**params)
    assert not serializer.is_valid()
    return serializer.errors


# --- parâmetros de consulta ----------------------------------------------


def test_empty_query_has_no_criteria():
    criteria = _valid()
    assert criteria.q is None and criteria.unit is None and not criteria.has_date_filter


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_search_and_neighborhood_become_none(value):
    criteria = _valid(q=value, neighborhood=value)
    assert criteria.q is None and criteria.neighborhood is None


def test_search_term_is_trimmed_and_limited_to_100():
    assert _valid(q="  dança ").q == "dança"
    assert _valid(q="a" * 100).q == "a" * 100
    assert "q" in _errors(q="a" * 101)


def test_neighborhood_limited_to_100():
    assert "neighborhood" in _errors(neighborhood="a" * 101)


def test_ids_must_be_uuids():
    wanted = uuid.uuid4()
    criteria = _valid(unit=str(wanted), category=str(wanted))
    assert criteria.unit == wanted and criteria.category == wanted
    errors = _errors(unit="abc", category="123")
    assert "unit" in errors and "category" in errors


def test_single_day_becomes_one_day_window():
    criteria = _valid(date="2026-11-20")
    assert criteria.date_from == criteria.date_to == date(2026, 11, 20)


def test_open_ended_windows_are_accepted():
    assert _valid(date_from="2026-11-20").date_to is None
    assert _valid(date_to="2026-11-20").date_from is None


def test_range_limits():
    assert _valid(date_from="2026-01-01", date_to="2027-01-02")  # 366 dias
    assert "date_to" in _errors(date_from="2026-01-01", date_to="2027-01-03")  # 367 dias
    assert "date_from" in _errors(date_from="2026-12-31", date_to="2026-12-01")


def test_day_cannot_be_combined_with_range():
    assert "date" in _errors(date="2026-11-20", date_from="2026-11-01")
    assert "date" in _errors(date="2026-11-20", date_to="2026-11-30")


@pytest.mark.parametrize("value", ["2026-13-40", "20/11/2026", "amanhã"])
def test_invalid_date_format(value):
    errors = _errors(date_from=value)
    assert errors["date_from"] == ["Informe uma data no formato AAAA-MM-DD."]


def test_unknown_parameters_are_ignored():
    assert _valid(foo="1", ordering="-title").q is None


# --- listagem ------------------------------------------------------------


def test_list_item_keys_and_formats():
    item = activity("Oficina de dança")
    data = ActivityListItemSerializer([(item, occurrence(date(2026, 11, 20)))], many=True).data
    assert list(data[0]) == [
        "id", "title", "slug", "summary", "unit", "category", "target_audiences",
        "next_occurrence", "image",
    ]  # fmt: skip
    assert set(data[0]["unit"]) == {"id", "name", "slug", "neighborhood"}
    assert set(data[0]["category"]) == {"id", "name", "slug"}
    assert dict(data[0]["next_occurrence"]) == {
        "date": "2026-11-20",
        "start_time": "14:00",
        "end_time": "15:00",
    }
    assert not _keys(data) & FORBIDDEN


def test_list_item_without_occurrence_has_null():
    data = ActivityListItemSerializer([(activity("A"), None)], many=True).data
    assert data[0]["next_occurrence"] is None


# --- detalhe -------------------------------------------------------------


def _detail(item, found=()):
    with patch.object(serializers, "activity_occurrences", return_value=list(found)) as calc:
        data = ActivityDetailSerializer(item).data
    return data, calc


def test_detail_keys_and_hidden_fields():
    item = activity("Oficina de dança", unit=unit(neighborhood="Grajaú"))
    data, _ = _detail(item)
    assert list(data) == [
        "id", "title", "slug", "summary", "description", "target_audience_notes", "unit",
        "category", "target_audiences", "external_registration_url", "image", "schedules",
        "next_occurrences",
    ]  # fmt: skip
    assert set(data["unit"]) == {"id", "name", "slug", "neighborhood", "address"}
    assert not _keys(data) & FORBIDDEN


def test_detail_audiences():
    audiences = [type("A", (), {"id": uuid.uuid4(), "name": "Adultos"})()]
    data, _ = _detail(activity("A", target_audiences=manager(audiences)))
    assert [dict(item)["name"] for item in data["target_audiences"]] == ["Adultos"]


def test_detail_schedules_sorted_with_weekday_names():
    late = recurring(date(2026, 12, 1), date(2026, 12, 31), [4, 2])
    early = one_time(date(2026, 11, 10))
    data, _ = _detail(activity("A", [late, early]))
    first, second = data["schedules"]
    assert first["schedule_type"] == "ONE_TIME" and first["start_date"] == "2026-11-10"
    assert first["weekdays"] == [] and first["weekday_names"] == []
    assert second["weekdays"] == [2, 4]
    assert second["weekday_names"] == ["Terça-feira", "Quinta-feira"]
    assert second["start_time"] == "14:00" and second["end_time"] == "15:00"


def test_detail_next_occurrences_limited_to_five():
    found = [occurrence(date(2026, 11, day)) for day in (10, 12)]
    data, calc = _detail(activity("A"), found)
    assert [item["date"] for item in data["next_occurrences"]] == ["2026-11-10", "2026-11-12"]
    assert calc.call_args.kwargs["limit"] == 5


def test_detail_without_future_dates():
    data, _ = _detail(activity("A"))
    assert data["next_occurrences"] == []


def test_detail_shows_inactive_unit_and_category():
    item = activity("A", unit=unit(is_active=False), category=category(is_active=False))
    data, _ = _detail(item)
    assert data["unit"]["name"] and data["category"]["name"]


# --- link externo --------------------------------------------------------


@pytest.mark.parametrize("url", ["https://exemplo.org/inscricao", "http://exemplo.org"])
def test_valid_external_links_are_delivered(url):
    data, _ = _detail(activity("A", external_registration_url=f" {url} "))
    assert data["external_registration_url"] == url


@pytest.mark.parametrize(
    "url", ["", "   ", "javascript:alert(1)", "ftp://exemplo.org", "exemplo.org", "//exemplo.org"]
)
def test_invalid_external_links_become_null(url):
    data, _ = _detail(activity("A", external_registration_url=url))
    assert "external_registration_url" in data
    assert data["external_registration_url"] is None


def test_missing_external_link_becomes_null():
    data, _ = _detail(activity("A", external_registration_url=None))
    assert data["external_registration_url"] is None


# --- unidades e categorias -----------------------------------------------


def test_unit_item_nullifies_empty_fields():
    data = UnitItemSerializer(unit(address="", description=""), many=False).data
    assert list(data) == ["id", "name", "slug", "neighborhood", "address", "description"]
    assert data["address"] is None and data["description"] is None
    assert not set(data) & FORBIDDEN


def test_unit_item_keeps_filled_fields():
    data = UnitItemSerializer(unit(address="Rua A", description="Texto")).data
    assert data["address"] == "Rua A" and data["description"] == "Texto"


def test_category_item():
    data = CategoryItemSerializer(category(description="")).data
    assert list(data) == ["id", "name", "slug", "description"]
    assert data["description"] is None
    assert CategoryItemSerializer(category(description="x")).data["description"] == "x"
