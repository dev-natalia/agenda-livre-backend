"""Auditoria de atividades e programações por todos os caminhos de escrita (sem banco)."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.contrib import admin
from django.test import RequestFactory
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from apps.activities import admin as activity_admin_module
from apps.activities.admin import ActivityAdmin
from apps.activities.models import Activity
from apps.activities.services import StatusChangeError, change_status
from apps.schedules.admin import ScheduleAdmin
from apps.schedules.models import Schedule

USER_A = SimpleNamespace(pk=1, username="a")
USER_B = SimpleNamespace(pk=2, username="b")


def _request(user):
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.parametrize(
    ("model_admin", "model"),
    [(ActivityAdmin, Activity), (ScheduleAdmin, Schedule)],
)
def test_save_model_creator_stays_and_updater_follows_the_editor(model_admin, model):
    instance = model_admin(model, admin.site)
    obj = SimpleNamespace()
    with patch.object(UnfoldModelAdmin, "save_model"):
        instance.save_model(_request(USER_A), obj, None, change=False)
        assert (obj.created_by, obj.updated_by) == (USER_A, USER_A)
        instance.save_model(_request(USER_B), obj, None, change=True)
    assert (obj.created_by, obj.updated_by) == (USER_A, USER_B)


def _saved(adding):
    return SimpleNamespace(_state=SimpleNamespace(adding=adding), save=MagicMock())


def test_inline_schedules_get_their_own_authorship():
    model_admin = ActivityAdmin(Activity, admin.site)
    new, old = _saved(True), _saved(False)
    old.created_by = USER_A
    formset = MagicMock(model=Schedule, deleted_objects=[], forms=[])
    formset.save.return_value = [new, old]
    with patch.object(activity_admin_module, "sync_weekdays"):
        model_admin.save_formset(_request(USER_B), None, formset, True)
    assert (new.created_by, new.updated_by) == (USER_B, USER_B)
    assert (old.created_by, old.updated_by) == (USER_A, USER_B)


def test_successful_status_change_records_who_and_when():
    activity = MagicMock(status=Activity.Status.PUBLISHED)
    assert change_status(activity, Activity.Status.CANCELLED, USER_B) is True
    assert activity.updated_by is USER_B
    fields = activity.save.call_args.kwargs["update_fields"]
    assert {"status", "updated_by", "updated_at"} <= set(fields)


def test_unchanged_or_refused_status_change_leaves_authorship_alone():
    same = MagicMock(status=Activity.Status.PUBLISHED, updated_by=USER_A)
    assert change_status(same, Activity.Status.PUBLISHED, USER_B) is False
    refused = MagicMock(status=Activity.Status.DRAFT, updated_by=USER_A)
    with pytest.raises(StatusChangeError):
        change_status(refused, Activity.Status.FINISHED, USER_B)
    for activity in (same, refused):
        assert activity.updated_by is USER_A
        activity.save.assert_not_called()


AUDIT_FIELDS = {"created_by", "updated_by", "created_at", "updated_at"}


@pytest.mark.parametrize(
    ("model_admin", "model"),
    [(ActivityAdmin, Activity), (ScheduleAdmin, Schedule)],
)
def test_audit_fields_are_read_only_in_the_admin(model_admin, model):
    assert AUDIT_FIELDS <= set(model_admin(model, admin.site).readonly_fields)


@pytest.mark.parametrize("model", [Activity, Schedule])
def test_authors_cannot_be_removed_and_fields_are_not_editable(model):
    for name in ("created_by", "updated_by"):
        field = model._meta.get_field(name)
        assert field.remote_field.on_delete.__name__ == "PROTECT"
        assert field.editable is False
    assert model._meta.get_field("created_at").auto_now_add is True
    assert model._meta.get_field("updated_at").auto_now is True
