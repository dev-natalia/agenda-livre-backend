"""Objetos em memória usados pelos testes da consulta pública (sem banco de dados)."""

import uuid
from datetime import datetime, time
from types import SimpleNamespace
from unittest.mock import MagicMock

from django.utils import timezone

from apps.activities.models import Activity
from apps.schedules.models import Schedule
from apps.schedules.services import Occurrence


def at(year, month, day, hour=0, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.get_current_timezone())


def manager(items):
    return MagicMock(all=lambda: list(items))


def unit(name="CEU Navegantes", neighborhood="Grajaú", **extra):
    values = {
        "id": uuid.uuid4(),
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "neighborhood": neighborhood,
        "address": "Rua Exemplo, 10",
        "description": "",
        "is_active": True,
    }
    values.update(extra)
    return SimpleNamespace(**values)


def category(name="Cultura e Artes", **extra):
    values = {
        "id": uuid.uuid4(),
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "description": "",
        "is_active": True,
    }
    values.update(extra)
    return SimpleNamespace(**values)


def schedule(kind, start, end, days=(), start_time=time(14), end_time=time(15)):
    return SimpleNamespace(
        id=uuid.uuid4(),
        schedule_type=kind,
        start_date=start,
        end_date=end,
        start_time=start_time,
        end_time=end_time,
        weekdays=manager([SimpleNamespace(weekday=day) for day in days]),
    )


def one_time(day, **extra):
    return schedule(Schedule.Type.ONE_TIME, day, day, **extra)


def recurring(start, end, days, **extra):
    return schedule(Schedule.Type.RECURRING, start, end, days=days, **extra)


def activity(title="Oficina de dança", schedules=(), status=Activity.Status.PUBLISHED, **extra):
    values = {
        "id": uuid.uuid4(),
        "title": title,
        "slug": title.lower().replace(" ", "-"),
        "summary": "Atividade aberta à comunidade.",
        "description": "Descrição completa.",
        "target_audience_notes": "",
        "external_registration_url": "",
        "status": status,
        "unit": unit(),
        "category": category(),
        "target_audiences": manager([]),
        "schedules": manager(schedules),
        "created_by": object(),
        "updated_at": object(),
    }
    values.update(extra)
    return SimpleNamespace(**values)


def occurrence(day, start=time(14), end=time(15)):
    return Occurrence(day, start, end, uuid.uuid4())

