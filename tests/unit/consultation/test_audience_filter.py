import uuid
from types import SimpleNamespace
from unittest.mock import patch

from consultation_helpers import activity, manager, unit

from apps.consultation import services
from apps.consultation.services import Criteria, apply_criteria, matches_audience


def audience(name, includes_everyone=False, is_active=True):
    pk = uuid.uuid4()
    return SimpleNamespace(
        pk=pk, id=pk, name=name, includes_everyone=includes_everyone, is_active=is_active
    )


def item(title, *audiences, **extra):
    return activity(title, target_audiences=manager(audiences), **extra)


ADULTS = audience("Adultos")
CHILDREN = audience("Crianças")
SENIORS = audience("Pessoas idosas")
EVERYONE = audience("Todas as idades", includes_everyone=True)


def run(items, chosen, **criteria):
    """Aplica o filtro de público com o público escolhido já resolvido (ou `None`)."""
    with patch.object(services, "find_audience", return_value=chosen) as find:
        result = apply_criteria(items, Criteria(audience=getattr(chosen, "pk", "x"), **criteria))
    return result, find


def titles(result):
    return [found.title for found in result]


def catalog():
    return [
        item("Para adultos", ADULTS),
        item("Para crianças", CHILDREN),
        item("Para todos", EVERYONE),
        item("Adultos e idosos", ADULTS, SENIORS),
        item("Sem público"),
    ]


# --- regra inclusiva -----------------------------------------------------


def test_specific_audience_includes_its_activities_and_the_everyone_ones():
    result, _ = run(catalog(), ADULTS)

    assert titles(result) == ["Para adultos", "Para todos", "Adultos e idosos"]


def test_specific_audience_excludes_other_specific_audiences():
    result, _ = run(catalog(), CHILDREN)

    assert titles(result) == ["Para crianças", "Para todos"]


def test_everyone_audience_returns_only_activities_linked_to_it():
    result, _ = run(catalog(), EVERYONE)

    assert titles(result) == ["Para todos"]


def test_activity_linked_to_the_chosen_and_to_everyone_appears_once():
    both = item("Adultos e todos", ADULTS, EVERYONE)

    result, _ = run([both, item("Outra", ADULTS)], ADULTS)

    assert titles(result) == ["Adultos e todos", "Outra"]


def test_activity_with_several_audiences_appears_once():
    several = item("Vários", ADULTS, SENIORS, CHILDREN)

    result, _ = run([several], SENIORS)

    assert titles(result) == ["Vários"]


def test_activity_without_audience_never_matches():
    result, _ = run([item("Sem público")], ADULTS)
    assert result == []
    result, _ = run([item("Sem público")], EVERYONE)
    assert result == []


def test_every_audience_marked_as_everyone_counts():
    other = audience("Para qualquer pessoa", includes_everyone=True)

    result, _ = run([item("A", other), item("B", EVERYONE), item("C", CHILDREN)], ADULTS)

    assert titles(result) == ["A", "B"]


def test_marked_audience_that_is_inactive_still_counts_when_linked():
    retired = audience("Todos (antigo)", includes_everyone=True, is_active=False)

    result, _ = run([item("Antiga", retired)], ADULTS)

    assert titles(result) == ["Antiga"]


def test_choosing_a_marked_audience_does_not_include_other_marked_ones():
    other = audience("Para qualquer pessoa", includes_everyone=True)

    result, _ = run([item("A", other), item("B", EVERYONE)], EVERYONE)

    assert titles(result) == ["B"]


# --- público inexistente ou inativo --------------------------------------


def test_missing_or_inactive_audience_returns_nothing_without_reading_activities():
    items = catalog()

    with patch.object(services, "find_audience", return_value=None) as find:
        result = apply_criteria(items, Criteria(audience=uuid.uuid4()))

    assert result == []
    find.assert_called_once()


# --- sem o filtro --------------------------------------------------------


def test_without_audience_nothing_is_filtered_and_no_lookup_is_made():
    items = catalog()

    with patch.object(services, "find_audience") as find:
        result = apply_criteria(items, Criteria())

    assert result == items
    find.assert_not_called()


def test_the_original_order_is_kept():
    items = [item("Z", ADULTS), item("A", EVERYONE), item("M", ADULTS)]

    result, _ = run(items, ADULTS)

    assert titles(result) == ["Z", "A", "M"]


def test_the_chosen_audience_is_looked_up_once():
    _, find = run(catalog(), ADULTS)

    find.assert_called_once_with(ADULTS.pk)


# --- combinação com busca e bairro ---------------------------------------


def test_audience_is_combined_with_search_and_neighborhood_by_and():
    here = unit(neighborhood="Grajaú")
    elsewhere = unit(name="CEU Outro", neighborhood="Santo Amaro")
    items = [
        item("Dança no Grajaú", ADULTS, unit=here),
        item("Dança em Santo Amaro", ADULTS, unit=elsewhere),
        item("Xadrez no Grajaú", ADULTS, unit=here),
        item("Dança infantil no Grajaú", CHILDREN, unit=here),
    ]

    result, _ = run(items, ADULTS, q="danca", neighborhood="grajau")

    assert titles(result) == ["Dança no Grajaú"]


# --- matches_audience e find_audience ------------------------------------


def test_matches_audience_follows_the_rule_table():
    assert matches_audience(item("A", ADULTS), ADULTS) is True
    assert matches_audience(item("A", EVERYONE), ADULTS) is True
    assert matches_audience(item("A", CHILDREN), ADULTS) is False
    assert matches_audience(item("A", ADULTS), EVERYONE) is False
    assert matches_audience(item("A", EVERYONE), EVERYONE) is True
    assert matches_audience(item("A"), ADULTS) is False


def test_find_audience_looks_for_an_active_audience_by_id():
    wanted = uuid.uuid4()

    with patch.object(services, "TargetAudience") as model:
        found = services.find_audience(wanted)

    model.objects.filter.assert_called_once_with(pk=wanted, is_active=True)
    assert found is model.objects.filter.return_value.first.return_value
