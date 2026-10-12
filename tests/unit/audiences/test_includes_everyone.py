from django.db import models

from apps.audiences.models import TargetAudience


def _field():
    return TargetAudience._meta.get_field("includes_everyone")


def test_field_is_a_boolean_off_by_default():
    assert isinstance(_field(), models.BooleanField)
    assert _field().default is False


def test_field_has_a_clear_label_and_help_text():
    assert _field().verbose_name == "Abrange todos os públicos"
    assert "Todas as idades" in _field().help_text


def test_new_audience_does_not_include_everyone():
    assert TargetAudience(name="Adultos").includes_everyone is False


def test_existing_fields_are_still_there():
    names = {field.name for field in TargetAudience._meta.get_fields()}

    assert {"id", "name", "slug", "description", "is_active"} <= names


def test_clean_still_builds_the_slug_and_keeps_the_mark():
    audience = TargetAudience(name="  Todas as idades ", includes_everyone=True)

    audience.clean()

    assert audience.slug == "todas-as-idades"
    assert audience.includes_everyone is True
