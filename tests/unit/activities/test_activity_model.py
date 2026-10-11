from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from apps.activities.models import PUBLIC_STATUSES, Activity, ActivityTargetAudience


def _activity(**kwargs):
    data = {"title": "Oficina de Teatro", "description": "Aulas de teatro."}
    data.update(kwargs)
    return Activity(**data)


def test_default_status_is_draft():
    assert Activity().status == Activity.Status.DRAFT


def test_status_values_and_labels():
    assert {choice.value: choice.label for choice in Activity.Status} == {
        "DRAFT": "Rascunho",
        "PUBLISHED": "Publicada",
        "FINISHED": "Encerrada",
        "CANCELLED": "Cancelada",
    }


def test_only_published_is_public():
    assert PUBLIC_STATUSES == {Activity.Status.PUBLISHED}


def test_str_is_title():
    assert str(_activity()) == "Oficina de Teatro"


def test_foreign_keys_are_protected():
    from django.db.models import PROTECT

    for name in ("unit", "category", "created_by", "updated_by"):
        assert Activity._meta.get_field(name).remote_field.on_delete is PROTECT


def test_indexes_and_unique_constraint_exist():
    assert {index.name for index in Activity._meta.indexes} == {
        "activity_status_idx",
        "activity_unit_status_idx",
        "activity_category_status_idx",
    }
    names = {constraint.name for constraint in ActivityTargetAudience._meta.constraints}
    assert names == {"unique_activity_target_audience"}


def test_status_slug_and_audit_fields_are_not_editable():
    for name in ("status", "slug", "created_by", "updated_by"):
        assert Activity._meta.get_field(name).editable is False


def test_clean_strips_text_and_generates_slug():
    activity = _activity(title="  Oficina de Teatro ", description=" Texto ")

    with patch.object(Activity, "_slug_taken", return_value=False):
        activity.clean()

    assert activity.title == "Oficina de Teatro"
    assert activity.description == "Texto"
    assert activity.slug == "oficina-de-teatro"


def test_clean_keeps_existing_slug():
    activity = _activity(slug="slug-antigo")

    with patch.object(Activity, "_slug_taken") as taken:
        activity.clean()

    assert activity.slug == "slug-antigo"
    taken.assert_not_called()


@pytest.mark.parametrize("field", ["title", "description"])
def test_clean_rejects_blank_required_text(field):
    activity = _activity(**{field: "   "})

    with pytest.raises(ValidationError) as error:
        activity.clean()

    assert field in error.value.message_dict


def test_clean_rejects_non_web_link():
    activity = _activity(external_registration_url="ftp://exemplo.org")

    with pytest.raises(ValidationError) as error:
        activity.clean()

    assert "external_registration_url" in error.value.message_dict


def test_clean_accepts_https_link():
    activity = _activity(external_registration_url="https://exemplo.org")

    with patch.object(Activity, "_slug_taken", return_value=False):
        activity.clean()

    assert activity.external_registration_url == "https://exemplo.org"


def test_slug_gets_numeric_suffix_on_collision():
    activity = _activity()

    with patch.object(Activity, "_slug_taken", side_effect=[True, True, False]):
        assert activity._build_slug() == "oficina-de-teatro-3"


def test_slug_falls_back_when_title_has_only_symbols():
    activity = _activity(title="!!!")

    with patch.object(Activity, "_slug_taken", return_value=False):
        assert activity._build_slug() == "atividade"


def test_slug_taken_excludes_current_record():
    activity = _activity()

    with patch.object(Activity, "objects") as manager:
        result = activity._slug_taken("x")

    manager.filter.assert_called_once_with(slug="x")
    manager.filter.return_value.exclude.assert_called_once_with(pk=activity.pk)
    assert result is manager.filter.return_value.exclude.return_value.exists.return_value
