from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from apps.activities.models import Activity
from apps.activities.services import StatusChangeError, change_status

Status = Activity.Status


def _activity(status=Status.DRAFT, **overrides):
    data = {
        "status": status,
        "title": "Oficina",
        "description": "Texto",
        "unit": SimpleNamespace(is_active=True),
        "category": SimpleNamespace(is_active=True),
        "audience_links": MagicMock(),
        "save": MagicMock(),
    }
    data["audience_links"].exists.return_value = True
    data.update(overrides)
    return SimpleNamespace(**data)


def test_publishes_complete_draft_and_records_audit():
    activity, user = _activity(), object()

    assert change_status(activity, Status.PUBLISHED, user) is True

    assert activity.status == Status.PUBLISHED
    assert activity.updated_by is user
    activity.save.assert_called_once_with(update_fields=["status", "updated_by", "updated_at"])


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"title": "  "}, "título"),
        ({"description": ""}, "descrição"),
        ({"unit": SimpleNamespace(is_active=False)}, "unidade"),
        ({"category": SimpleNamespace(is_active=False)}, "categoria"),
    ],
)
def test_publication_is_refused_for_invalid_data(overrides, message):
    activity = _activity(**overrides)

    with pytest.raises(StatusChangeError, match=message):
        change_status(activity, Status.PUBLISHED, object())

    activity.save.assert_not_called()
    assert activity.status == Status.DRAFT


def test_publication_is_refused_without_audience():
    activity = _activity()
    activity.audience_links.exists.return_value = False

    with pytest.raises(StatusChangeError, match="público-alvo"):
        change_status(activity, Status.PUBLISHED, object())

    activity.save.assert_not_called()


@pytest.mark.parametrize("new_status", list(Status))
def test_same_status_is_a_noop(new_status):
    activity = _activity(status=new_status)

    assert change_status(activity, new_status, object()) is False

    activity.save.assert_not_called()


@pytest.mark.parametrize("new_status", [Status.CANCELLED, Status.FINISHED])
def test_published_can_be_cancelled_or_finished(new_status):
    activity = _activity(status=Status.PUBLISHED)

    assert change_status(activity, new_status, object()) is True

    assert activity.status == new_status
    activity.save.assert_called_once_with(update_fields=["status", "updated_by", "updated_at"])


@pytest.mark.parametrize("old_status", [Status.CANCELLED, Status.FINISHED])
def test_cancelled_or_finished_can_be_republished(old_status):
    activity = _activity(status=old_status)

    assert change_status(activity, Status.PUBLISHED, object()) is True

    assert activity.status == Status.PUBLISHED


@pytest.mark.parametrize(
    ("old_status", "new_status"),
    [
        (Status.DRAFT, Status.CANCELLED),
        (Status.DRAFT, Status.FINISHED),
        (Status.FINISHED, Status.CANCELLED),
        (Status.CANCELLED, Status.FINISHED),
        (Status.PUBLISHED, Status.DRAFT),
    ],
)
def test_disallowed_transitions_are_refused(old_status, new_status):
    activity = _activity(status=old_status)

    with pytest.raises(StatusChangeError, match="Não é possível passar de"):
        change_status(activity, new_status, object())

    activity.save.assert_not_called()
