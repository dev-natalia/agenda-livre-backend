from django.db.models import UniqueConstraint
from django.db.models.functions import Lower

from apps.categories.models import Category
from apps.core.models import CatalogModel


def test_category_extends_catalog_model():
    assert issubclass(Category, CatalogModel)


def test_name_is_unique_ignoring_case_via_constraint():
    (constraint,) = Category._meta.constraints
    assert isinstance(constraint, UniqueConstraint)
    assert constraint.name == "category_name_ci_unique"
    assert constraint.expressions == (Lower("name"),)


def test_slug_is_unique():
    assert Category._meta.get_field("slug").unique is True


def test_verbose_names_and_ordering():
    assert Category._meta.verbose_name == "Categoria"
    assert Category._meta.verbose_name_plural == "Categorias"
    assert Category._meta.ordering == ["name"]


def test_clean_generates_slug_and_strips_name():
    category = Category(name=" Saúde e Bem-estar ")

    category.clean()

    assert category.name == "Saúde e Bem-estar"
    assert category.slug == "saude-e-bem-estar"
