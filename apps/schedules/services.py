from dataclasses import dataclass
from datetime import date, time, timedelta
from itertools import islice

from django.db.models import prefetch_related_objects
from django.utils import timezone

from apps.activities.models import PUBLIC_STATUSES
from apps.schedules.models import Schedule, ScheduleWeekday

WEEKDAY_ABBREVIATIONS = {1: "Seg", 2: "Ter", 3: "Qua", 4: "Qui", 5: "Sex", 6: "Sáb", 7: "Dom"}


@dataclass(frozen=True)
class Occurrence:
    date: date
    start_time: time
    end_time: time
    schedule_id: object


def iter_occurrences(schedule, weekdays, from_date, to_date=None):
    """Gera, em ordem de data, as ocorrências da programação em [`from_date`, `to_date`]."""
    if schedule.schedule_type == Schedule.Type.ONE_TIME:
        if schedule.start_date >= from_date and (to_date is None or schedule.start_date <= to_date):
            yield _occurrence(schedule, schedule.start_date)
        return
    current = max(schedule.start_date, from_date)
    last = schedule.end_date if to_date is None else min(schedule.end_date, to_date)
    while current <= last:
        if current.isoweekday() in weekdays:
            yield _occurrence(schedule, current)
        current += timedelta(days=1)


def _occurrence(schedule, day):
    return Occurrence(day, schedule.start_time, schedule.end_time, schedule.id)


def activity_occurrences(activity, now=None, date_from=None, date_to=None, limit=None):
    """Ocorrências ainda não encerradas na janela, em ordem; vazio se a atividade não é pública."""
    if limit is not None and limit < 1:
        raise ValueError("limit deve ser positivo.")
    if activity.status not in PUBLIC_STATUSES:
        return []
    now = timezone.localtime(now or timezone.now())
    today, current_time = now.date(), now.time()
    start = max(date_from, today) if date_from else today
    if date_to is not None and date_to < start:
        return []
    prefetch_related_objects([activity], "schedules__weekdays")
    found = []
    for schedule in activity.schedules.all():
        weekdays = {item.weekday for item in schedule.weekdays.all()}
        pending = (
            occurrence
            for occurrence in iter_occurrences(schedule, weekdays, start, date_to)
            if not (occurrence.date == today and occurrence.end_time <= current_time)
        )
        found.extend(islice(pending, limit))
    found.sort(key=lambda item: (item.date, item.start_time))
    return found[:limit]


def upcoming_occurrences(activity, now=None, limit=10):
    """Próximas ocorrências ainda não encerradas; vazio se a atividade não é pública."""
    if limit < 1:
        raise ValueError("limit deve ser positivo.")
    return activity_occurrences(activity, now=now, limit=limit)


def format_weekdays(schedule):
    """Nomes abreviados dos dias da programação, ou "—" quando não houver."""
    days = sorted(item.weekday for item in schedule.weekdays.all())
    return ", ".join(WEEKDAY_ABBREVIATIONS[day] for day in days) or "—"


def sync_weekdays(schedule, chosen):
    """Deixa os dias gravados da programação exatamente iguais aos escolhidos."""
    chosen = set(chosen or [])
    current = set(schedule.weekdays.values_list("weekday", flat=True))
    if current - chosen:
        schedule.weekdays.filter(weekday__in=current - chosen).delete()
    missing = sorted(chosen - current)
    if missing:
        ScheduleWeekday.objects.bulk_create(
            [ScheduleWeekday(schedule=schedule, weekday=day) for day in missing]
        )
