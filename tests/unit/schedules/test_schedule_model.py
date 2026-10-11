from datetime import date, time

import pytest
from django.core.exceptions import ValidationError
from django.db import models

from apps.activities.models import Activity
from apps.schedules.models import Schedule, ScheduleWeekday

Type = Schedule.Type


def _schedule(**overrides):
    values = {
        "schedule_type": Type.RECURRING,
        "start_date": date(2026, 11, 1),
        "end_date": date(2026, 11, 30),
        "start_time": time(14),
        "end_time": time(15),
    }
    values.update(overrides)
    return Schedule(**values)


def _errors(schedule):
    with pytest.raises(ValidationError) as info:
        schedule.clean()
    return info.value.message_dict


def test_type_labels():
    assert Type.ONE_TIME.label == "Pontual"
    assert Type.RECURRING.label == "Recorrente"


def test_str():
    schedule = _schedule(activity=Activity(title="Capoeira"))
    assert str(schedule) == "Capoeira (Recorrente)"


def test_meta():
    meta = Schedule._meta
    assert meta.ordering == ["start_date", "start_time"]
    assert meta.verbose_name == "Programação"
    assert meta.verbose_name_plural == "Programações"
    assert {c.name for c in meta.constraints} == {
        "schedule_dates_ordered",
        "schedule_times_ordered",
        "schedule_one_time_single_date",
    }
    assert {i.name for i in meta.indexes} == {"schedule_activity_idx", "schedule_period_idx"}


def test_activity_relation_is_protected():
    field = Schedule._meta.get_field("activity")
    assert field.remote_field.on_delete is models.PROTECT
    assert field.remote_field.related_name == "schedules"


def test_valid_recurring_and_one_time():
    _schedule().clean()
    _schedule(schedule_type=Type.ONE_TIME, end_date=date(2026, 11, 1)).clean()


def test_rejects_inverted_period():
    errors = _errors(_schedule(start_date=date(2026, 12, 1)))
    assert errors["end_date"] == ["A data final não pode ser anterior à data inicial."]


@pytest.mark.parametrize("end", [time(14), time(13), time(1)])
def test_rejects_end_time_not_after_start(end):
    errors = _errors(_schedule(end_time=end))
    assert errors["end_time"] == ["O horário de término deve ser posterior ao de início."]


def test_midnight_crossing_is_rejected():
    errors = _errors(_schedule(start_time=time(23), end_time=time(1)))
    assert "end_time" in errors


def test_one_time_requires_same_date():
    errors = _errors(_schedule(schedule_type=Type.ONE_TIME))
    assert errors["end_date"] == ["Em programação pontual, a data final deve ser igual à inicial."]


def test_reports_several_errors_at_once():
    errors = _errors(_schedule(start_date=date(2026, 12, 1), end_time=time(13)))
    assert set(errors) == {"end_date", "end_time"}


def test_skips_validation_when_a_field_is_missing():
    _schedule(end_time=None).clean()
    _schedule(start_date=None).clean()


def test_weekday_choices():
    values = [value for value, _ in ScheduleWeekday.Weekday.choices]
    labels = [label for _, label in ScheduleWeekday.Weekday.choices]
    assert values == [1, 2, 3, 4, 5, 6, 7]
    assert labels[0] == "Segunda-feira"
    assert labels[-1] == "Domingo"


def test_weekday_meta():
    meta = ScheduleWeekday._meta
    assert {c.name for c in meta.constraints} == {
        "unique_schedule_weekday",
        "schedule_weekday_range",
    }
    assert meta.ordering == ["weekday"]
    assert meta.verbose_name == "Dia da semana"
    field = meta.get_field("schedule")
    assert field.remote_field.on_delete is models.CASCADE
    assert field.remote_field.related_name == "weekdays"


def test_weekday_str():
    assert str(ScheduleWeekday(weekday=2)) == "Terça-feira"
