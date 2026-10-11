from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.contrib import admin
from django.test import RequestFactory

from apps.schedules import admin as schedule_admin_module
from apps.schedules.admin import ScheduleAdmin
from apps.schedules.forms import ScheduleAdminForm
from apps.schedules.models import Schedule


@pytest.fixture
def model_admin():
    return ScheduleAdmin(Schedule, admin.site)


def _request():
    request = RequestFactory().get("/")
    request.user = SimpleNamespace(pk=1)
    return request


def test_is_registered(model_admin):
    assert isinstance(admin.site._registry[Schedule], ScheduleAdmin)
    assert model_admin.form is ScheduleAdminForm


def test_list_configuration(model_admin):
    assert model_admin.list_display == (
        "activity",
        "schedule_type",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "weekday_names",
        "updated_at",
    )
    assert model_admin.list_filter == ("schedule_type", "start_date", "end_date")
    assert model_admin.search_fields == ("activity__title",)
    assert model_admin.list_select_related == ("activity",)
    assert model_admin.autocomplete_fields == ("activity",)


def test_form_configuration(model_admin):
    assert model_admin.readonly_fields == ("created_by", "updated_by", "created_at", "updated_at")
    assert model_admin.fields[:7] == (
        "activity",
        "schedule_type",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "weekdays",
    )


def test_get_queryset_prefetches_weekdays(model_admin):
    queryset = MagicMock()
    with patch.object(admin.ModelAdmin, "get_queryset", return_value=queryset):
        result = model_admin.get_queryset(_request())
    queryset.prefetch_related.assert_called_once_with("weekdays")
    assert result is queryset.prefetch_related.return_value


def test_weekday_names_column(model_admin):
    schedule = SimpleNamespace(weekdays=MagicMock(all=lambda: [SimpleNamespace(weekday=2)]))
    assert model_admin.weekday_names(schedule) == "Ter"


def test_save_model_on_create_sets_both_users(model_admin):
    request, obj = _request(), SimpleNamespace()
    with patch.object(admin.ModelAdmin, "save_model") as parent:
        model_admin.save_model(request, obj, None, change=False)
    assert obj.created_by is request.user
    assert obj.updated_by is request.user
    parent.assert_called_once()


def test_save_model_on_edit_keeps_creator(model_admin):
    request, obj = _request(), SimpleNamespace(created_by="original")
    with patch.object(admin.ModelAdmin, "save_model"):
        model_admin.save_model(request, obj, None, change=True)
    assert obj.created_by == "original"
    assert obj.updated_by is request.user


def test_save_related_syncs_chosen_weekdays(model_admin):
    schedule = object()
    form = SimpleNamespace(instance=schedule, cleaned_data={"weekdays": [2, 4]})
    with patch.object(admin.ModelAdmin, "save_related"), patch.object(
        schedule_admin_module, "sync_weekdays"
    ) as sync:
        model_admin.save_related(_request(), form, [], change=True)
    sync.assert_called_once_with(schedule, [2, 4])
