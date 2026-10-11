from datetime import date, datetime, time, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from apps.activities.models import Activity
from apps.schedules import services
from apps.schedules.models import Schedule
from apps.schedules.services import (
    Occurrence,
    format_weekdays,
    iter_occurrences,
    sync_weekdays,
    upcoming_occurrences,
)

Type = Schedule.Type


def _weekdays(days):
    return MagicMock(all=lambda: [SimpleNamespace(weekday=d) for d in days])


def _schedule(kind, start, end, start_time=time(14), end_time=time(15), days=()):
    return SimpleNamespace(
        id=object(),
        schedule_type=kind,
        start_date=start,
        end_date=end,
        start_time=start_time,
        end_time=end_time,
        weekdays=_weekdays(days),
    )


def _activity(schedules, status=Activity.Status.PUBLISHED):
    activity = SimpleNamespace(status=status)
    activity.schedules = MagicMock()
    activity.schedules.prefetch_related.return_value = schedules
    return activity


def _at(year, month, day, hour=0, minute=0):
    zone = services.timezone.get_current_timezone()
    return datetime(year, month, day, hour, minute, tzinfo=zone)


def _dates(result):
    return [item.date for item in result]


def test_one_time_future_and_past():
    schedule = _schedule(Type.ONE_TIME, date(2026, 11, 10), date(2026, 11, 10))
    found = list(iter_occurrences(schedule, set(), date(2026, 11, 10)))
    assert _dates(found) == [date(2026, 11, 10)]
    assert list(iter_occurrences(schedule, set(), date(2026, 11, 11))) == []


def test_one_time_ignores_weekdays():
    schedule = _schedule(Type.ONE_TIME, date(2026, 11, 10), date(2026, 11, 10))
    assert len(list(iter_occurrences(schedule, {1}, date(2026, 11, 1)))) == 1


def test_recurring_tuesdays_and_thursdays():
    schedule = _schedule(Type.RECURRING, date(2026, 11, 1), date(2026, 11, 30))
    result = list(iter_occurrences(schedule, {2, 4}, date(2026, 11, 9)))
    assert [o.date.day for o in result] == [10, 12, 17, 19, 24, 26]
    assert result[0] == Occurrence(date(2026, 11, 10), time(14), time(15), schedule.id)


def test_recurring_bounds_are_inclusive():
    schedule = _schedule(Type.RECURRING, date(2026, 11, 3), date(2026, 11, 10))
    result = list(iter_occurrences(schedule, {2}, date(2026, 1, 1)))
    assert _dates(result) == [date(2026, 11, 3), date(2026, 11, 10)]


def test_recurring_without_matching_day_is_empty():
    schedule = _schedule(Type.RECURRING, date(2026, 11, 2), date(2026, 11, 4))
    assert list(iter_occurrences(schedule, {6}, date(2026, 11, 1))) == []


def test_recurring_in_the_past_is_empty():
    schedule = _schedule(Type.RECURRING, date(2026, 1, 1), date(2026, 1, 31))
    assert list(iter_occurrences(schedule, {1, 2, 3, 4, 5, 6, 7}, date(2026, 11, 1))) == []


def test_upcoming_one_time_today_not_finished_yet():
    schedule = _schedule(Type.ONE_TIME, date(2026, 11, 10), date(2026, 11, 10))
    result = upcoming_occurrences(_activity([schedule]), now=_at(2026, 11, 10, 14, 30))
    assert _dates(result) == [date(2026, 11, 10)]


def test_upcoming_one_time_today_already_finished():
    schedule = _schedule(Type.ONE_TIME, date(2026, 11, 10), date(2026, 11, 10))
    assert upcoming_occurrences(_activity([schedule]), now=_at(2026, 11, 10, 15, 0)) == []


def test_upcoming_recurring_example():
    schedule = _schedule(Type.RECURRING, date(2026, 11, 1), date(2026, 11, 30), days=[2, 4])
    result = upcoming_occurrences(_activity([schedule]), now=_at(2026, 11, 9), limit=20)
    assert [d.day for d in _dates(result)] == [10, 12, 17, 19, 24, 26]


@pytest.mark.parametrize(
    "status", [Activity.Status.DRAFT, Activity.Status.CANCELLED, Activity.Status.FINISHED]
)
def test_upcoming_empty_when_not_published(status):
    schedule = _schedule(Type.ONE_TIME, date(2026, 11, 10), date(2026, 11, 10))
    assert upcoming_occurrences(_activity([schedule], status), now=_at(2026, 11, 1)) == []


def test_upcoming_orders_by_date_then_start_time():
    first = _schedule(Type.ONE_TIME, date(2026, 11, 10), date(2026, 11, 10), time(16), time(17))
    second = _schedule(Type.ONE_TIME, date(2026, 11, 10), date(2026, 11, 10), time(9), time(10))
    third = _schedule(Type.ONE_TIME, date(2026, 11, 9), date(2026, 11, 9), time(20), time(21))
    result = upcoming_occurrences(_activity([first, second, third]), now=_at(2026, 11, 1))
    assert [(o.date.day, o.start_time.hour) for o in result] == [(9, 20), (10, 9), (10, 16)]


def test_upcoming_limit():
    schedule = _schedule(Type.RECURRING, date(2026, 11, 1), date(2026, 11, 30), days=[1, 2, 3])
    assert len(upcoming_occurrences(_activity([schedule]), now=_at(2026, 11, 1), limit=3)) == 3


def test_upcoming_invalid_limit():
    with pytest.raises(ValueError):
        upcoming_occurrences(_activity([]), limit=0)


def test_upcoming_converts_now_to_local_timezone():
    schedule = _schedule(Type.ONE_TIME, date(2026, 11, 9), date(2026, 11, 9), time(22), time(23))
    late = datetime(2026, 11, 10, 2, 0, tzinfo=timezone.utc)  # 23:00 do dia 9 em São Paulo
    assert upcoming_occurrences(_activity([schedule]), now=late) == []
    early = datetime(2026, 11, 10, 0, 30, tzinfo=timezone.utc)  # 21:30 do dia 9 em São Paulo
    assert len(upcoming_occurrences(_activity([schedule]), now=early)) == 1


def test_upcoming_default_now_uses_timezone_now():
    with patch.object(services.timezone, "now", return_value=_at(2026, 11, 1)) as clock:
        assert upcoming_occurrences(_activity([])) == []
    clock.assert_called_once()


def test_upcoming_without_schedules():
    assert upcoming_occurrences(_activity([]), now=_at(2026, 11, 1)) == []


def test_format_weekdays():
    assert format_weekdays(SimpleNamespace(weekdays=_weekdays([4, 2]))) == "Ter, Qui"
    every_day = SimpleNamespace(weekdays=_weekdays([1, 2, 3, 4, 5, 6, 7]))
    assert format_weekdays(every_day) == "Seg, Ter, Qua, Qui, Sex, Sáb, Dom"
    assert format_weekdays(SimpleNamespace(weekdays=_weekdays([]))) == "—"


def _sync(chosen, current):
    schedule = MagicMock()
    schedule.weekdays.values_list.return_value = current
    with patch.object(services, "ScheduleWeekday") as weekday_model:
        sync_weekdays(schedule, chosen)
    return schedule, weekday_model


def test_sync_creates_only_missing_days():
    schedule, model = _sync([2, 4], [2])
    model.assert_called_once_with(schedule=schedule, weekday=4)
    model.objects.bulk_create.assert_called_once()
    schedule.weekdays.filter.assert_not_called()


def test_sync_removes_only_extra_days():
    schedule, model = _sync([4, 6], [2, 4])
    schedule.weekdays.filter.assert_called_once_with(weekday__in={2})
    schedule.weekdays.filter.return_value.delete.assert_called_once()
    model.assert_called_once_with(schedule=schedule, weekday=6)


def test_sync_changes_nothing_when_sets_match():
    schedule, model = _sync([2, 4], [4, 2])
    model.objects.bulk_create.assert_not_called()
    schedule.weekdays.filter.assert_not_called()


def test_sync_empty_or_missing_clears_days():
    schedule, model = _sync([], [2, 4])
    schedule.weekdays.filter.assert_called_once_with(weekday__in={2, 4})
    model.objects.bulk_create.assert_not_called()
    schedule, _ = _sync(None, [3])
    schedule.weekdays.filter.assert_called_once_with(weekday__in={3})
