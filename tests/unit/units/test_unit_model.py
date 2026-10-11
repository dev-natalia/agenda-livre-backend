from apps.core.models import CatalogModel
from apps.units.models import Unit


def test_unit_extends_catalog_model():
    assert issubclass(Unit, CatalogModel)


def test_neighborhood_is_required_and_limited():
    field = Unit._meta.get_field("neighborhood")
    assert field.blank is False
    assert field.max_length == 100


def test_address_is_optional():
    assert Unit._meta.get_field("address").blank is True


def test_slug_unique_and_name_not_unique():
    assert Unit._meta.get_field("slug").unique is True
    assert Unit._meta.get_field("name").unique is False


def test_clean_strips_neighborhood_and_generates_slug():
    unit = Unit(name=" CEU Navegantes ", neighborhood="  Navegantes ")

    unit.clean()

    assert unit.neighborhood == "Navegantes"
    assert unit.slug == "ceu-navegantes"


def test_verbose_names_and_ordering():
    assert Unit._meta.verbose_name == "Unidade"
    assert Unit._meta.verbose_name_plural == "Unidades"
    assert Unit._meta.ordering == ["name"]
