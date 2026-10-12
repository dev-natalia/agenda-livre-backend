from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command

from apps.core.management.commands import seed_catalog

UNIT_SLUGS = ["ceu-navegantes"]
CATEGORY_SLUGS = [
    "cultura-e-artes",
    "cursos-e-formacao",
    "esporte-e-atividade-fisica",
    "lazer-e-recreacao",
    "saude-e-bem-estar",
    "educacao-e-meio-ambiente",
    "eventos-e-encontros",
    "participacao-comunitaria",
]


def _run(created):
    unit_manager, category_manager, audience_manager = MagicMock(), MagicMock(), MagicMock()
    for manager in (unit_manager, category_manager, audience_manager):
        manager.get_or_create.return_value = (MagicMock(), created)
    out = StringIO()
    with (
        patch.object(seed_catalog.Unit, "objects", unit_manager),
        patch.object(seed_catalog.Category, "objects", category_manager),
        patch.object(seed_catalog.TargetAudience, "objects", audience_manager),
    ):
        call_command("seed_catalog", stdout=out)
    _run.audience_manager = audience_manager
    return unit_manager, category_manager, out.getvalue()


def test_loads_one_unit_and_eight_categories_by_slug():
    unit_manager, category_manager, _ = _run(True)

    unit_slugs = [c.kwargs["slug"] for c in unit_manager.get_or_create.call_args_list]
    category_slugs = [c.kwargs["slug"] for c in category_manager.get_or_create.call_args_list]
    assert unit_slugs == UNIT_SLUGS
    assert category_slugs == CATEGORY_SLUGS


def test_reports_created_records():
    _, _, output = _run(True)

    assert "Unidades: 1 criada(s), 0 já existiam." in output
    assert "Categorias: 8 criada(s), 0 já existiam." in output


def test_reports_existing_records_and_never_updates_them():
    unit_manager, category_manager, output = _run(False)

    assert "Unidades: 0 criada(s), 1 já existiam." in output
    assert "Categorias: 0 criada(s), 8 já existiam." in output
    assert not unit_manager.update_or_create.called
    assert not category_manager.update_or_create.called


def test_unit_defaults_include_required_fields():
    unit_manager, _, _ = _run(True)

    defaults = unit_manager.get_or_create.call_args.kwargs["defaults"]
    assert defaults == {"name": "CEU Navegantes", "neighborhood": "Cantinho do Céu"}


AUDIENCE_SLUGS = ["criancas", "adolescentes", "adultos", "pessoas-idosas", "todas-as-idades"]


def test_loads_target_audiences_by_slug():
    _run(True)

    calls = _run.audience_manager.get_or_create.call_args_list
    assert [c.kwargs["slug"] for c in calls] == AUDIENCE_SLUGS


def test_reports_target_audiences():
    _, _, created = _run(True)
    _, _, existing = _run(False)

    assert "Públicos-alvo: 5 criada(s), 0 já existiam." in created
    assert "Públicos-alvo: 0 criada(s), 5 já existiam." in existing


# --- marca "abrange todos" ------------------------------------------------


def test_only_all_ages_is_declared_as_including_everyone():
    marked = [a["slug"] for a in seed_catalog.TARGET_AUDIENCES if a.get("includes_everyone")]

    assert marked == ["todas-as-idades"]
    assert all(
        "includes_everyone" not in a
        for a in seed_catalog.TARGET_AUDIENCES
        if a["slug"] != "todas-as-idades"
    )


def test_all_ages_is_created_with_the_mark():
    _run(True)

    calls = _run.audience_manager.get_or_create.call_args_list
    by_slug = {c.kwargs["slug"]: c.kwargs["defaults"] for c in calls}
    assert by_slug["todas-as-idades"]["includes_everyone"] is True
    assert "includes_everyone" not in by_slug["adultos"]


def test_existing_all_ages_without_the_mark_gets_it():
    _run(False)

    manager = _run.audience_manager
    manager.filter.assert_called_once_with(slug="todas-as-idades")
    manager.filter.return_value.update.assert_called_once_with(includes_everyone=True)


def test_the_mark_is_never_removed_from_any_audience():
    _run(False)
    _run(True)

    for call in _run.audience_manager.filter.return_value.update.call_args_list:
        assert call.kwargs == {"includes_everyone": True}


def test_marking_does_not_touch_units_or_categories():
    unit_manager, category_manager, _ = _run(False)

    assert not unit_manager.filter.called and not category_manager.filter.called


def test_running_twice_reports_the_same_and_creates_nothing():
    _, _, first = _run(False)
    _, _, second = _run(False)

    assert first == second
    assert "Públicos-alvo: 0 criada(s), 5 já existiam." in second
