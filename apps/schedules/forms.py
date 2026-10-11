from django import forms

from apps.schedules.models import Schedule, ScheduleWeekday


class ScheduleAdminForm(forms.ModelForm):
    weekdays = forms.TypedMultipleChoiceField(
        label="Dias da semana",
        choices=ScheduleWeekday.Weekday.choices,
        coerce=int,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Obrigatório para programações recorrentes. Deve ficar vazio nas pontuais.",
    )

    class Meta:
        model = Schedule
        fields = ("activity", "schedule_type", "start_date", "end_date", "start_time", "end_time")

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
