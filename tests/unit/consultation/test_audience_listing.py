import uuid
from types import SimpleNamespace
from unittest.mock import patch

from consultation_helpers import activity, manager

from apps.consultation import services
from apps.consultation.serializers import (
    ActivityDetailSerializer,
    ActivityListItemSerializer,
    audiences_payload,
)
from apps.consultation.services import published_activities


def _audience(name):
    pk = uuid.uuid4()
    return SimpleNamespace(pk=pk, id=pk, name=name, includes_everyone=False, is_active=True)


def _item(*audiences, **extra):
    return activity("Oficina", target_audiences=manager(audiences), **extra)


def _listed(item):
    return ActivityListItemSerializer(instance=(item, None)).data


def _detail(item):
    with patch("apps.consultation.serializers.activity_occurrences", return_value=[]):
        return ActivityDetailSerializer(item).data


# --- payload -------------------------------------------------------------


def test_payload_has_id_and_name_only_sorted_by_name():
    adults, children, seniors = _audience("Adultos"), _audience("Crianças"), _audience("Idosos")

    payload = audiences_payload(_item(seniors, adults, children))

    assert payload == [
        {"id": adults.id, "name": "Adultos"},
        {"id": children.id, "name": "Crianças"},
        {"id": seniors.id, "name": "Idosos"},
    ]


def test_payload_is_an_empty_list_without_audiences():
    assert audiences_payload(_item()) == []


# --- listagem ------------------------------------------------------------


def test_list_item_has_the_audiences_key_sorted_by_name():
    adults, children = _audience("Adultos"), _audience("Crianças")

    data = _listed(_item(children, adults))

    assert [found["name"] for found in data["target_audiences"]] == ["Adultos", "Crianças"]
    assert set(data["target_audiences"][0]) == {"id", "name"}


def test_list_item_without_audiences_has_an_empty_list_never_none():
    data = _listed(_item())

    assert "target_audiences" in data
    assert data["target_audiences"] == []


def test_existing_list_fields_are_unchanged():
    data = _listed(_item(_audience("Adultos")))

    assert set(data) == {
        "id",
        "title",
        "slug",
        "summary",
        "unit",
        "category",
        "target_audiences",
        "next_occurrence",
        "image",
    }


def test_free_text_about_the_audience_stays_only_in_the_detail():
    item = _item(_audience("Adultos"), target_audience_notes="Iniciantes são bem-vindos.")

    assert "target_audience_notes" not in _listed(item)
    assert _detail(item)["target_audience_notes"] == "Iniciantes são bem-vindos."


# --- detalhe -------------------------------------------------------------


def test_detail_uses_the_same_sorted_payload():
    adults, children = _audience("Adultos"), _audience("Crianças")

    data = _detail(_item(children, adults))

    assert data["target_audiences"] == _listed(_item(children, adults))["target_audiences"]
    assert [found["name"] for found in data["target_audiences"]] == ["Adultos", "Crianças"]


def test_detail_without_audiences_has_an_empty_list():
    assert _detail(_item())["target_audiences"] == []


# --- sem consulta extra por atividade -----------------------------------


def test_audiences_are_loaded_together_with_the_other_relations():
    with patch.object(services, "Activity") as model:
        published_activities()

    select = model.objects.filter.return_value.select_related
    select.assert_called_once_with("unit", "category")
    select.return_value.prefetch_related.assert_called_once_with(
        "schedules__weekdays", "target_audiences"
    )
