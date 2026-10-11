from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError

from apps.activities.models import Activity
from apps.activities.services import StatusChangeError, change_status


def _activity(**extra):
    values = {
        "title": "Oficina",
        "slug": "oficina",
        "description": "Texto",
        "external_registration_url": "",
    }
    values.update(extra)
    return Activity(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    [("title", "   "), ("description", "  \n ")],
)
def test_blank_required_text_is_rejected_on_the_field(field, value):
    with pytest.raises(ValidationError) as error:
        _activity(**{field: value}).clean()
    assert field in error.value.message_dict


@pytest.mark.parametrize(
    "url",
    ["ftp://exemplo.com/x", "javascript:alert(1)", "exemplo.com/inscricao", "file:///etc/passwd"],
)
def test_non_web_urls_are_rejected(url):
    with pytest.raises(ValidationError) as error:
        _activity(external_registration_url=url).clean()
    assert "external_registration_url" in error.value.message_dict


@pytest.mark.parametrize("url", ["http://exemplo.com/x", "https://exemplo.com/x", ""])
def test_web_urls_and_blank_are_accepted(url):
    _activity(external_registration_url=url).clean()


def test_refused_status_change_does_not_touch_the_activity():
    activity = MagicMock(status=Activity.Status.DRAFT, updated_by="antes")
    with pytest.raises(StatusChangeError) as error:
        change_status(activity, Activity.Status.CANCELLED, SimpleNamespace(pk=2))
    assert "Rascunho" in str(error.value) and "Cancelada" in str(error.value)
    assert activity.updated_by == "antes"
    activity.save.assert_not_called()
