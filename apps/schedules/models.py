import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Schedule(models.Model):
    class Type(models.TextChoices):
        ONE_TIME = "ONE_TIME", "Pontual"
        RECURRING = "RECURRING", "Recorrente"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(
        "activities.Activity",
        verbose_name="Atividade",
        on_delete=models.PROTECT,
        related_name="schedules",
    )
    schedule_type = models.CharField("Tipo", max_length=20, choices=Type.choices)
    start_date = models.DateField("Data inicial")
    end_date = models.DateField("Data final")
    start_time = models.TimeField("Horário de início")
    end_time = models.TimeField("Horário de término")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Criada por",
        on_delete=models.PROTECT,
        related_name="+",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Atualizada por",
        on_delete=models.PROTECT,
        related_name="+",
        editable=False,
    )
    created_at = models.DateTimeField("Criada em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizada em", auto_now=True)

    class Meta:
        verbose_name = "Programação"
        verbose_name_plural = "Programações"
        ordering = ["start_date", "start_time"]
        constraints = [
            models.CheckConstraint(
                condition=Q(start_date__lte=F("end_date")), name="schedule_dates_ordered"
            ),
            models.CheckConstraint(
                condition=Q(start_time__lt=F("end_time")), name="schedule_times_ordered"
            ),
            models.CheckConstraint(
                condition=~Q(schedule_type="ONE_TIME") | Q(start_date=F("end_date")),
                name="schedule_one_time_single_date",
            ),
        ]
        indexes = [
            models.Index(fields=["activity"], name="schedule_activity_idx"),
            models.Index(fields=["start_date", "end_date"], name="schedule_period_idx"),
        ]

    def __str__(self):
        return f"{self.activity} ({self.get_schedule_type_display()})"

    def clean(self):
        super().clean()
        if None in (self.start_date, self.end_date, self.start_time, self.end_time):
            return
        errors = {}
        if self.start_date > self.end_date:
            errors["end_date"] = "A data final não pode ser anterior à data inicial."
        elif self.schedule_type == self.Type.ONE_TIME and self.start_date != self.end_date:
            errors["end_date"] = "Em programação pontual, a data final deve ser igual à inicial."
        if self.start_time >= self.end_time:
            errors["end_time"] = "O horário de término deve ser posterior ao de início."
        if errors:
            raise ValidationError(errors)


class ScheduleWeekday(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, "Segunda-feira"
        TUESDAY = 2, "Terça-feira"
        WEDNESDAY = 3, "Quarta-feira"
        THURSDAY = 4, "Quinta-feira"
        FRIDAY = 5, "Sexta-feira"
        SATURDAY = 6, "Sábado"
        SUNDAY = 7, "Domingo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(
        Schedule,
        verbose_name="Programação",
        on_delete=models.CASCADE,
        related_name="weekdays",
    )
    weekday = models.PositiveSmallIntegerField("Dia da semana", choices=Weekday.choices)

    class Meta:
        verbose_name = "Dia da semana"
        verbose_name_plural = "Dias da semana"
        ordering = ["weekday"]
        constraints = [
            models.UniqueConstraint(fields=["schedule", "weekday"], name="unique_schedule_weekday"),
            models.CheckConstraint(
                condition=Q(weekday__gte=1) & Q(weekday__lte=7), name="schedule_weekday_range"
            ),
        ]

    def __str__(self):
        return self.get_weekday_display()
