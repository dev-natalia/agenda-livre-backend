from datetime import date, time
from unittest.mock import patch

import pytest
from consultation_helpers import activity, at, occurrence, one_time, recurring, unit

from apps.activities.models import PUBLIC_STATUSES
from apps.consultation import services
from apps.consultation.services import (
    Criteria,
    apply_criteria,
    build_listing,
    matches_search,
    normalize_text,
    published_activities,
    reference_occurrence,
)


@pytest.fixture(autouse=True)
def _no_prefetch():
    with patch("apps.schedules.services.prefetch_related_objects"):
        yield


NOW = at(2026, 11, 9)


def _titles(pairs):
    return [pair[0].title for pair in pairs]


def test_normalize_text():
    assert normalize_text("Dança") == "danca"
    assert normalize_text("  Ação ") == "acao"
    assert normalize_text(None) == ""


def test_listing_orders_by_date_then_time_then_title():
    late = activity("Zumba", [one_time(date(2026, 11, 12))])
    early = activity("Yoga", [one_time(date(2026, 11, 10))])
    same_day_b = activity("Balé", [one_time(date(2026, 11, 10))])
    same_day_a = activity("Ábaco", [one_time(date(2026, 11, 10))])
    morning_schedule = one_time(date(2026, 11, 10), start_time=time(9), end_time=time(10))
    morning = activity("Teatro", [morning_schedule])
    result = build_listing([late, early, same_day_b, same_day_a, morning], NOW)
    assert _titles(result) == ["Teatro", "Ábaco", "Balé", "Yoga", "Zumba"]


def test_activities_without_occurrence_come_last_in_alphabetical_order():
    past = activity("Zeta", [one_time(date(2026, 1, 1))])
    none = activity("Árvore", [])
    upcoming = activity("Yoga", [one_time(date(2026, 11, 20))])
    result = build_listing([past, none, upcoming], NOW)
    assert _titles(result) == ["Yoga", "Árvore", "Zeta"]
    assert [pair[1] is None for pair in result] == [False, True, True]


def test_listing_of_empty_input():
    assert build_listing([], NOW) == []


def test_listing_passes_window_to_occurrence_service():
    item = activity("Yoga")
    with patch.object(services, "activity_occurrences", return_value=[]) as calc:
        build_listing([item], NOW, date(2026, 11, 10), date(2026, 11, 12))
    calc.assert_called_once_with(
        item, now=NOW, date_from=date(2026, 11, 10), date_to=date(2026, 11, 12), limit=1
    )


def test_reference_occurrence_is_none_without_dates():
    assert reference_occurrence(activity("Yoga"), NOW) is None


def test_reference_occurrence_returns_first():
    found = [occurrence(date(2026, 11, 10)), occurrence(date(2026, 11, 12))]
    with patch.object(services, "activity_occurrences", return_value=found):
        assert reference_occurrence(activity("Yoga"), NOW) is found[0]


# --- busca ---------------------------------------------------------------


@pytest.mark.parametrize("field", ["title", "summary", "description"])
def test_search_matches_each_field(field):
    item = activity("Xadrez", summary="resumo", description="texto", **{})
    setattr(item, field, "Oficina de dança")
    assert matches_search(item, "dança")


def test_search_ignores_case_and_accents():
    item = activity("Oficina de dança")
    assert matches_search(item, "danca")
    assert matches_search(item, "DANÇA")
    assert matches_search(activity("Oficina de danca"), "dança")


def test_search_without_match():
    assert not matches_search(activity("Xadrez"), "dança")


@pytest.mark.parametrize("term", [None, "", "   "])
def test_empty_term_matches_everything(term):
    assert matches_search(activity("Xadrez"), term)


@pytest.mark.parametrize("term", ["%", "'", '"', ";--", "\\", "a|b", "(.*)"])
def test_special_characters_are_plain_text(term):
    assert not matches_search(activity("Xadrez"), term)
    literal = activity("Curso (.*) a|b ;-- \\ % ' \"")
    assert matches_search(literal, term)


def test_apply_criteria_search_only():
    items = [activity("Dança"), activity("Xadrez")]
    assert _titles([(a, None) for a in apply_criteria(items, Criteria(q="danca"))]) == ["Dança"]
    assert len(apply_criteria(items, Criteria())) == 2


# --- bairro --------------------------------------------------------------


def test_neighborhood_filter_ignores_accents_and_case():
    here = activity("A", unit=unit(neighborhood="Grajaú"))
    other = activity("B", unit=unit(neighborhood="Santo Amaro"))
    assert apply_criteria([here, other], Criteria(neighborhood="grajau")) == [here]
    assert apply_criteria([here, other], Criteria(neighborhood=None)) == [here, other]


# --- consulta ao banco ---------------------------------------------------


def test_published_activities_filters_status_and_chains_optional_filters():
    with patch.object(services, "Activity") as model:
        base = model.objects.filter.return_value.select_related.return_value
        queryset = base.prefetch_related.return_value
        published_activities()
        model.objects.filter.assert_called_once_with(status__in=PUBLIC_STATUSES)
        queryset.filter.assert_not_called()
        published_activities(Criteria(unit="u", category="c"))
        queryset.filter.assert_called_once_with(unit_id="u")
        queryset.filter.return_value.filter.assert_called_once_with(category_id="c")


def test_published_activities_category_only():
    with patch.object(services, "Activity") as model:
        queryset = model.objects.filter.return_value.select_related.return_value.prefetch_related
        queryset = queryset.return_value
        published_activities(Criteria(category="c"))
        queryset.filter.assert_called_once_with(category_id="c")


# --- filtro de data ------------------------------------------------------


def _recurring():
    return recurring(date(2026, 11, 1), date(2026, 12, 31), [2, 4])


def test_date_filter_one_time():
    item = activity("A", [one_time(date(2026, 11, 20))])
    assert len(build_listing([item], NOW, date(2026, 11, 20), date(2026, 11, 20))) == 1
    assert build_listing([item], NOW, date(2026, 11, 21), date(2026, 11, 21)) == []


def test_date_filter_recurring_inside_and_outside():
    item = activity("A", [_recurring()])
    tuesday = date(2026, 11, 17)
    assert len(build_listing([item], NOW, tuesday, tuesday)) == 1
    wednesday = date(2026, 11, 18)
    assert build_listing([item], NOW, wednesday, wednesday) == []
    outside = date(2027, 1, 5)
    assert build_listing([item], NOW, outside, outside) == []


def test_date_filter_range_is_inclusive_and_uses_first_in_window():
    item = activity("A", [_recurring()])
    result = build_listing([item], NOW, date(2026, 11, 11), date(2026, 11, 12))
    assert result[0][1].date == date(2026, 11, 12)
    edge = build_listing([item], NOW, date(2026, 11, 12), date(2026, 11, 12))
    assert len(edge) == 1


def test_date_filter_today_finished_does_not_count():
    item = activity("A", [one_time(date(2026, 11, 10))])
    today = date(2026, 11, 10)
    assert build_listing([item], at(2026, 11, 10, 15), today, today) == []
    assert len(build_listing([item], at(2026, 11, 10, 14, 30), today, today)) == 1


def test_date_filter_in_the_past_is_empty():
    item = activity("A", [one_time(date(2026, 11, 1))])
    day = date(2026, 11, 1)
    assert build_listing([item], NOW, day, day) == []


def test_date_filter_orders_by_first_occurrence_in_window():
    first = activity("Z", [one_time(date(2026, 11, 20))])
    second = activity("A", [one_time(date(2026, 11, 25))])
    result = build_listing([second, first], NOW, date(2026, 11, 15), date(2026, 11, 30))
    assert _titles(result) == ["Z", "A"]


def test_open_ended_windows():
    item = activity("A", [one_time(date(2026, 11, 20))])
    assert len(build_listing([item], NOW, date_from=date(2026, 11, 15))) == 1
    assert len(build_listing([item], NOW, date_to=date(2026, 11, 30))) == 1
    assert build_listing([item], NOW, date_to=date(2026, 11, 10)) == []


def test_without_date_filter_activities_without_dates_stay_in_list():
    assert len(build_listing([activity("A", [])], NOW)) == 1


@pytest.mark.parametrize("status", ["DRAFT", "CANCELLED", "FINISHED"])
def test_non_published_never_have_occurrences(status):
    item = activity("A", [one_time(date(2026, 11, 20))], status=status)
    assert build_listing([item], NOW, date(2026, 11, 20), date(2026, 11, 20)) == []


# --- combinações ---------------------------------------------------------


def _catalog():
    grajau = unit(neighborhood="Grajaú")
    santo = unit("CEU Outro", neighborhood="Santo Amaro")
    return [
        activity("Dança infantil", [one_time(date(2026, 11, 20))], unit=grajau),
        activity("Dança adulto", [one_time(date(2026, 11, 21))], unit=santo),
        activity("Xadrez", [one_time(date(2026, 11, 20))], unit=grajau),
        activity("Dança sem data", [], unit=grajau),
    ]


def _run(criteria):
    filtered = apply_criteria(_catalog(), criteria)
    return _titles(build_listing(filtered, NOW, criteria.date_from, criteria.date_to))


def test_combined_filters_use_and():
    day = date(2026, 11, 20)
    assert _run(Criteria(q="danca", neighborhood="grajau", date_from=day, date_to=day)) == [
        "Dança infantil"
    ]
    assert _run(Criteria(q="danca", neighborhood="santo amaro", date_from=day, date_to=day)) == []


def test_removing_a_criterion_never_shrinks_the_result():
    day = date(2026, 11, 20)
    full = Criteria(q="danca", neighborhood="grajau", date_from=day, date_to=day)
    steps = [
        full,
        Criteria(q="danca", neighborhood="grajau"),
        Criteria(q="danca"),
        Criteria(),
    ]
    sizes = [len(_run(criteria)) for criteria in steps]
    assert sizes == sorted(sizes)
    assert sizes[-1] == 4


def test_criteria_has_date_filter():
    assert not Criteria().has_date_filter
    assert Criteria(date_from=date(2026, 1, 1)).has_date_filter
    assert Criteria(date_to=date(2026, 1, 1)).has_date_filter


def test_search_term_is_not_sent_to_the_database():
    with patch.object(services, "Activity") as model:
        published_activities(Criteria(q="'; DROP TABLE x;--"))
    queryset = model.objects.filter.return_value.select_related.return_value.prefetch_related
    queryset.return_value.filter.assert_not_called()
