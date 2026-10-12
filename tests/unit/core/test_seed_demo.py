from datetime import date, time
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.management.commands import seed_catalog, seed_demo

CATALOG_UNITS = {unit["slug"] for unit in seed_catalog.UNITS}
CATEGORIES = {c["slug"] for c in seed_catalog.CATEGORIES}
AUDIENCES = {a["slug"] for a in seed_catalog.TARGET_AUDIENCES}
TODAY = date(2026, 10, 11)


def test_new_units_have_the_requested_addresses_and_phones():
    by_slug = {unit["slug"]: unit for unit in seed_demo.UNITS}
    assert set(by_slug) == {"ceu-cidade-dutra", "ceu-vila-rubi", "ceu-vila-do-sol"}
    assert "Av. Interlagos, 7350" in by_slug["ceu-cidade-dutra"]["address"]
    assert by_slug["ceu-cidade-dutra"]["description"] == "Telefone: (11) 5668-1935"
    assert "R. Domingos Tarroso, 101" in by_slug["ceu-vila-rubi"]["address"]
    assert by_slug["ceu-vila-rubi"]["description"] == "Telefone: (11) 5662-9400"
    assert "Av. dos Funcionários Públicos, 369" in by_slug["ceu-vila-do-sol"]["address"]
    assert by_slug["ceu-vila-do-sol"]["description"] == "Telefone: (11) 3397-9800"
    assert all(unit["neighborhood"] for unit in seed_demo.UNITS)


def test_activities_reference_known_units_categories_and_audiences():
    units = CATALOG_UNITS | {unit["slug"] for unit in seed_demo.UNITS}
    for item in seed_demo.ACTIVITIES:
        assert item["unit"] in units
        assert item["category"] in CATEGORIES
        assert item["audiences"] and set(item["audiences"]) <= AUDIENCES


def test_titles_are_unique_and_within_model_limits():
    titles = [item["title"] for item in seed_demo.ACTIVITIES]
    assert len(titles) == len(set(titles))
    for item in seed_demo.ACTIVITIES:
        assert len(item["title"]) <= 200
        assert len(item["summary"]) <= 300
        assert item["description"].strip()
        assert item.get("external", "https://").startswith("https://")


def test_data_covers_every_unit_and_every_status():
    assert {i["unit"] for i in seed_demo.ACTIVITIES} == CATALOG_UNITS | {
        u["slug"] for u in seed_demo.UNITS
    }
    assert {i["status"] for i in seed_demo.ACTIVITIES} == {
        seed_demo.DRAFT,
        seed_demo.PUBLISHED,
        seed_demo.FINISHED,
        seed_demo.CANCELLED,
    }


def test_schedules_respect_the_model_constraints():
    for item in seed_demo.ACTIVITIES:
        assert item["schedules"]
        for plan in item["schedules"]:
            assert plan["from_days"] <= plan["to_days"]
            assert time.fromisoformat(plan["start"]) < time.fromisoformat(plan["end"])
            if plan["type"] == "ONE_TIME":
                assert plan["from_days"] == plan["to_days"]
                assert "weekdays" not in plan
            else:
                assert plan["type"] == "RECURRING"
                assert plan["to_days"] - plan["from_days"] >= 6
                assert plan["weekdays"]
                assert len(set(plan["weekdays"])) == len(plan["weekdays"])
                assert all(1 <= day <= 7 for day in plan["weekdays"])


def test_finished_activities_are_in_the_past_and_published_ones_have_future_dates():
    for item in seed_demo.ACTIVITIES:
        last = max(plan["to_days"] for plan in item["schedules"])
        if item["status"] == seed_demo.FINISHED:
            assert last < 0
        if item["status"] == seed_demo.PUBLISHED:
            assert last > 0


def test_admin_user_is_the_oldest_active_staff_and_no_user_is_created():
    manager = MagicMock()
    ordered = manager.filter.return_value.order_by.return_value
    ordered.first.return_value = "admin"
    with patch.object(seed_demo, "get_user_model", return_value=SimpleNamespace(objects=manager)):
        assert seed_demo._admin_user() == "admin"
    manager.filter.assert_called_once_with(is_staff=True, is_active=True)
    manager.create.assert_not_called()
    manager.create_user.assert_not_called()


def test_missing_admin_stops_with_a_clear_message():
    manager = MagicMock()
    manager.filter.return_value.order_by.return_value.first.return_value = None
    with patch.object(seed_demo, "get_user_model", return_value=SimpleNamespace(objects=manager)):
        with pytest.raises(CommandError, match="create_admin"):
            seed_demo._admin_user()


def test_missing_catalog_asks_for_seed_catalog():
    model = MagicMock()
    model.objects.filter.return_value = [SimpleNamespace(slug="a")]
    with pytest.raises(CommandError, match="seed_catalog"):
        seed_demo._by_slug(model, {"a", "b"}, "Categoria")


def test_by_slug_returns_a_mapping():
    item = SimpleNamespace(slug="a")
    model = MagicMock()
    model.objects.filter.return_value = [item]
    assert seed_demo._by_slug(model, {"a"}, "X") == {"a": item}


def test_create_schedules_builds_weekdays_only_for_recurring():
    plans = [
        seed_demo.one_time(3, "10:00", "11:00"),
        seed_demo.recurring(-2, 40, [2, 4], "18:00", "19:30"),
    ]
    with (
        patch.object(seed_demo.Schedule, "objects") as schedules,
        patch.object(seed_demo, "ScheduleWeekday", side_effect=lambda **kw: kw) as weekday_cls,
    ):
        created = []
        weekday_cls.objects.bulk_create.side_effect = lambda items: created.append(list(items))
        seed_demo._create_schedules("atividade", plans, TODAY, "admin")
    first, second = schedules.create.call_args_list
    assert first.kwargs["start_date"] == first.kwargs["end_date"] == date(2026, 10, 14)
    assert first.kwargs["schedule_type"] == "ONE_TIME"
    assert second.kwargs["start_date"] == date(2026, 10, 9)
    assert second.kwargs["end_date"] == date(2026, 11, 20)
    assert second.kwargs["start_time"] == time(18, 0)
    assert second.kwargs["created_by"] == second.kwargs["updated_by"] == "admin"
    assert created[0] == []
    assert [w["weekday"] for w in created[1]] == [2, 4]


def test_create_activity_links_audiences_and_schedules():
    item = seed_demo.ACTIVITIES[0]
    units = {item["unit"]: "unidade"}
    categories = {item["category"]: "categoria"}
    audiences = {slug: f"pub-{slug}" for slug in item["audiences"]}
    with (
        patch.object(seed_demo, "Activity") as activity_cls,
        patch.object(seed_demo.ActivityTargetAudience, "objects") as links,
        patch.object(seed_demo, "_create_schedules") as schedules,
    ):
        seed_demo._create_activity(item, units, categories, audiences, TODAY, "admin")
    kwargs = activity_cls.call_args.kwargs
    assert kwargs["title"] == item["title"]
    assert kwargs["status"] == item["status"]
    assert kwargs["unit"] == "unidade" and kwargs["category"] == "categoria"
    assert kwargs["created_by"] == kwargs["updated_by"] == "admin"
    activity = activity_cls.return_value
    activity.clean.assert_called_once()
    activity.save.assert_called_once()
    assert links.create.call_count == len(item["audiences"])
    schedules.assert_called_once_with(activity, item["schedules"], TODAY, "admin")


def _run(existing):
    out = StringIO()
    with (
        patch.object(seed_demo, "_admin_user", return_value="admin"),
        patch.object(seed_demo, "_load", return_value=(3, 0)) as load,
        patch.object(seed_demo, "_by_slug", return_value=MagicMock()),
        patch.object(seed_demo.Activity, "objects") as activities,
        patch.object(seed_demo, "_create_activity") as create,
        patch.object(seed_demo, "_attach_demo_images", return_value=(0, 0)),
        patch.object(seed_demo.transaction, "atomic"),
    ):
        activities.filter.return_value.exists.return_value = existing
        call_command("seed_demo", stdout=out)
    return load, create, out.getvalue()


def test_command_creates_every_activity_when_none_exist():
    load, create, output = _run(existing=False)
    assert load.call_args.args[1] == seed_demo.UNITS
    assert create.call_count == len(seed_demo.ACTIVITIES)
    assert f"Atividades: {len(seed_demo.ACTIVITIES)} criada(s), 0 já existiam." in output
    assert "Unidades: 3 criada(s), 0 já existiam." in output


def test_command_is_safe_to_repeat():
    _, create, output = _run(existing=True)
    create.assert_not_called()
    assert f"Atividades: 0 criada(s), {len(seed_demo.ACTIVITIES)} já existiam." in output
