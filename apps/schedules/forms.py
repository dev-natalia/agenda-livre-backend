from django import forms

from apps.schedules.models import Schedule, ScheduleWeekday

SCHEDULE_FIELDS = ("schedule_type", "start_date", "end_date", "start_time", "end_time")


class WeekdaysFormMixin(forms.ModelForm):
    """Campo de dias da semana e regras que cruzam o tipo da programação e os dias."""

    weekdays = forms.TypedMultipleChoiceField(
        label="Dias da semana",
        choices=ScheduleWeekday.Weekday.choices,
        coerce=int,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Obrigatório para programações recorrentes. Deve ficar vazio nas pontuais.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance._state.adding:
            days = self.instance.weekdays.values_list("weekday", flat=True)
            self.initial["weekdays"] = list(days)

    def clean(self):
        cleaned = super().clean()
        schedule_type = cleaned.get("schedule_type")
        days = set(cleaned.get("weekdays") or [])
        if schedule_type == Schedule.Type.RECURRING and not days:
            self.add_error("weekdays", "Selecione ao menos um dia da semana.")
        elif schedule_type == Schedule.Type.ONE_TIME and days:
            self.add_error("weekdays", "Programação pontual não usa dias da semana.")
        return cleaned


class ScheduleAdminForm(WeekdaysFormMixin):
    class Meta:
        model = Schedule
        fields = ("activity", *SCHEDULE_FIELDS)


class ScheduleInlineForm(WeekdaysFormMixin):
    """Formulário da programação dentro da página da atividade (a atividade vem do inline)."""

    class Meta:
        model = Schedule
        fields = SCHEDULE_FIELDS
