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


def _form(chosen, current):
    schedule = MagicMock()
    schedule.weekdays.values_list.return_value = current
    form = SimpleNamespace(instance=schedule, cleaned_data={"weekdays": chosen})
    return form, schedule


def _save_related(model_admin, form):
    with patch.object(admin.ModelAdmin, "save_related"), patch.object(
        schedule_admin_module, "ScheduleWeekday"
    ) as weekday_model:
        model_admin.save_related(_request(), form, [], change=True)
    weekday_model.objects.created = [
        call.kwargs["weekday"] for call in weekday_model.call_args_list
    ]
    return weekday_model.objects.bulk_create, weekday_model


def test_save_related_creates_only_missing_days(model_admin):
    form, schedule = _form([2, 4], [2])
    bulk, weekday_model = _save_related(model_admin, form)
    weekday_model.assert_called_once_with(schedule=schedule, weekday=4)
    bulk.assert_called_once()
    schedule.weekdays.filter.assert_not_called()


def test_save_related_removes_only_extra_days(model_admin):
    form, schedule = _form([4, 6], [2, 4])
    bulk, weekday_model = _save_related(model_admin, form)
    schedule.weekdays.filter.assert_called_once_with(weekday__in={2})
    schedule.weekdays.filter.return_value.delete.assert_called_once()
    weekday_model.assert_called_once_with(schedule=schedule, weekday=6)
    bulk.assert_called_once()


def test_save_related_changes_nothing_when_sets_match(model_admin):
    form, schedule = _form([2, 4], [4, 2])
    bulk, _ = _save_related(model_admin, form)
    bulk.assert_not_called()
    schedule.weekdays.filter.assert_not_called()


def test_save_related_switch_to_one_time_clears_days(model_admin):
    form, schedule = _form([], [2, 4])
    bulk, _ = _save_related(model_admin, form)
    schedule.weekdays.filter.assert_called_once_with(weekday__in={2, 4})
    bulk.assert_not_called()


def test_save_related_missing_cleaned_value_means_no_days(model_admin):
    form, schedule = _form(None, [3])
    _save_related(model_admin, form)
    schedule.weekdays.filter.assert_called_once_with(weekday__in={3})
