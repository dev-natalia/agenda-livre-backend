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
