import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from consultation_helpers import activity, manager, occurrence, unit
from rest_framework.test import APIClient

from apps.consultation import services, views
from apps.consultation.services import (
    Criteria,
    apply_criteria,
    build_listing,
    published_activities,
)

client = APIClient()


def _audience(name, includes_everyone=False):
    pk = uuid.uuid4()
    return SimpleNamespace(pk=pk, id=pk, name=name, includes_everyone=includes_everyone)


ADULTS = _audience("Adultos")
EVERYONE = _audience("Todas as idades", includes_everyone=True)


def _item(title, *audiences, **extra):
    return activity(title, target_audiences=manager(audiences), **extra)


# --- unidade e categoria vêm do banco; o público é filtrado depois ----------


def test_unit_and_category_still_narrow_the_query_and_the_audience_filters_the_rest():
    criteria = Criteria(unit="u", category="c", audience=ADULTS.pk)

    with patch.object(services, "Activity") as model:
        chain = model.objects.filter.return_value.select_related.return_value
        queryset = chain.prefetch_related.return_value
        published_activities(criteria)

    queryset.filter.assert_called_once_with(unit_id="u")
    queryset.filter.return_value.filter.assert_called_once_with(category_id="c")
    with patch.object(services, "find_audience", return_value=ADULTS):
        kept = apply_criteria(
            [_item("Para adultos", ADULTS), _item("Para outro público", _audience("X"))], criteria
        )
    assert [found.title for found in kept] == ["Para adultos"]


def test_audience_search_and_neighborhood_are_all_applied():
    here, elsewhere = unit(neighborhood="Grajaú"), unit(name="Outro", neighborhood="Santo Amaro")
    items = [
        _item("Dança no Grajaú", ADULTS, unit=here),
        _item("Dança para todos no Grajaú", EVERYONE, unit=here),
        _item("Dança em Santo Amaro", ADULTS, unit=elsewhere),
        _item("Xadrez no Grajaú", ADULTS, unit=here),
    ]

    with patch.object(services, "find_audience", return_value=ADULTS):
        criteria = Criteria(audience=ADULTS.pk, q="danca", neighborhood="grajau")
        result = apply_criteria(items, criteria)

    assert [found.title for found in result] == ["Dança no Grajaú", "Dança para todos no Grajaú"]


# --- datas e ordenação ---------------------------------------------------


def test_date_window_and_audience_keep_the_sort_by_next_occurrence():
    early, late = occurrence(date(2026, 11, 3)), occurrence(date(2026, 11, 20))
    items = [_item("B tarde", ADULTS), _item("A cedo", EVERYONE), _item("Fora", _audience("X"))]
    window = {"B tarde": late, "A cedo": early}
    criteria = Criteria(audience=ADULTS.pk, date_from=date(2026, 11, 1), date_to=date(2026, 11, 30))

    with (
        patch.object(services, "find_audience", return_value=ADULTS),
        patch.object(
            services,
            "reference_occurrence",
            side_effect=lambda found, *args, **kwargs: window.get(found.title),
        ),
    ):
        kept = apply_criteria(items, criteria)
        listing = build_listing(kept, None, criteria.date_from, criteria.date_to)

    assert [found.title for found, _ in listing] == ["A cedo", "B tarde"]


# --- ponta a ponta -------------------------------------------------------


@pytest.fixture
def catalog():
    items = [_item("Para adultos", ADULTS), _item("Para todos", EVERYONE)]
    with (
        patch.object(views, "published_activities", return_value=items),
        patch("apps.consultation.services.activity_occurrences", return_value=[]),
        patch.object(services, "find_audience", return_value=ADULTS),
    ):
        yield items


def test_date_with_a_range_is_still_refused_when_audience_is_present(catalog):
    response = client.get(
        f"/api/v1/activities/?audience={ADULTS.pk}&date=2026-11-01&date_from=2026-11-01"
    )

    assert response.status_code == 400
    assert set(response.json()["errors"]) == {"date"}


def test_several_invalid_parameters_are_reported_each_on_its_field(catalog):
    response = client.get("/api/v1/activities/?audience=abc&unit=x&date_from=2026-13-40")

    assert response.status_code == 400
    assert set(response.json()["errors"]) == {"audience", "unit", "date_from"}


def test_valid_combination_returns_only_the_activities_that_match_all(catalog):
    response = client.get(
        f"/api/v1/activities/?audience={ADULTS.pk}&q=adultos&neighborhood=Grajau"
        f"&unit={uuid.uuid4()}&category={uuid.uuid4()}"
    )

    assert response.status_code == 200
    # "Para todos" também é do público, mas não contém "adultos": a busca por texto o exclui.
    assert [found["title"] for found in response.json()["results"]] == ["Para adultos"]
