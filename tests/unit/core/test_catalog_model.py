import pytest
from django.core.exceptions import ValidationError

from apps.core.models import CatalogModel


class _Item(CatalogModel):
    class Meta(CatalogModel.Meta):
        app_label = "core"


def test_clean_strips_name_and_generates_slug():
    item = _Item(name="  Cultura e Artes  ")

    item.clean()

    assert item.name == "Cultura e Artes"
    assert item.slug == "cultura-e-artes"


def test_clean_keeps_informed_slug():
    item = _Item(name="Cultura e Artes", slug="cultura")

    item.clean()

    assert item.slug == "cultura"


def test_clean_rejects_name_without_usable_slug():
    item = _Item(name="!!!")

    with pytest.raises(ValidationError) as error:
        item.clean()

    assert "slug" in error.value.message_dict


def test_str_is_the_name():
    assert str(_Item(name="CEU")) == "CEU"


def test_meta_is_abstract_and_ordered_by_name():
    assert CatalogModel._meta.abstract is True
    assert _Item._meta.ordering == ["name"]


def test_slug_is_unique_and_name_is_not():
    assert _Item._meta.get_field("slug").unique is True
    assert _Item._meta.get_field("name").unique is False
