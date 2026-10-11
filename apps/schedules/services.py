from dataclasses import dataclass
from datetime import date, time, timedelta

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


def iter_occurrences(schedule, weekdays, from_date):
    """Gera, em ordem de data, as ocorrências da programação a partir de `from_date`."""
    if schedule.schedule_type == Schedule.Type.ONE_TIME:
        if schedule.start_date >= from_date:
            yield _occurrence(schedule, schedule.start_date)
        return
    current = max(schedule.start_date, from_date)
    while current <= schedule.end_date:
        if current.isoweekday() in weekdays:
            yield _occurrence(schedule, current)
        current += timedelta(days=1)


def _occurrence(schedule, day):
    return Occurrence(day, schedule.start_time, schedule.end_time, schedule.id)


def upcoming_occurrences(activity, now=None, limit=10):
    """Próximas ocorrências ainda não encerradas; vazio se a atividade não é pública."""
    if limit < 1:
        raise ValueError("limit deve ser positivo.")
    if activity.status not in PUBLIC_STATUSES:
        return []
    now = timezone.localtime(now or timezone.now())
    today, current_time = now.date(), now.time()
    found = []
    for schedule in activity.schedules.prefetch_related("weekdays"):
        weekdays = {item.weekday for item in schedule.weekdays.all()}
        for occurrence in iter_occurrences(schedule, weekdays, today):
            if occurrence.date == today and occurrence.end_time <= current_time:
                continue
            found.append(occurrence)
    found.sort(key=lambda item: (item.date, item.start_time))
    return found[:limit]


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
