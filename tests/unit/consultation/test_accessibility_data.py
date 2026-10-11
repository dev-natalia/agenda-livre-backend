"""Dados públicos legíveis por pessoas: textos, formatos inequívocos e vazios como `null`."""

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from consultation_helpers import activity, category, manager, one_time, recurring, unit

from apps.consultation import serializers
from apps.consultation.serializers import (
    ActivityDetailSerializer,
    CategoryItemSerializer,
    UnitItemSerializer,
)


def _detail(item):
    with patch.object(serializers, "activity_occurrences", return_value=[]):
        return ActivityDetailSerializer(item).data


def test_detail_carries_human_readable_names():
    audience = SimpleNamespace(id=uuid.uuid4(), name="Adultos")
    item = activity(
        "Oficina",
        [recurring(date(2026, 11, 1), date(2026, 12, 1), [2, 4])],
        target_audiences=manager([audience]),
    )
    data = _detail(item)
    assert data["unit"]["name"] and data["category"]["name"]
    assert [entry["name"] for entry in data["target_audiences"]] == ["Adultos"]
    assert data["schedules"][0]["weekday_names"] == ["Terça-feira", "Quinta-feira"]


def test_dates_and_times_use_unambiguous_formats():
    data = _detail(activity("Oficina", [one_time(date(2026, 11, 10))]))
    schedule = data["schedules"][0]
    assert schedule["start_date"] == "2026-11-10"
    assert schedule["start_time"] == "14:00" and schedule["end_time"] == "15:00"


def test_empty_optional_fields_are_null_not_blank_text():
    assert _detail(activity("Oficina"))["external_registration_url"] is None
    blank_unit = UnitItemSerializer(unit(address="", description="")).data
    assert blank_unit["address"] is None and blank_unit["description"] is None
    assert CategoryItemSerializer(category(description="")).data["description"] is None
