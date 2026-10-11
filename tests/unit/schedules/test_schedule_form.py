from datetime import date, time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django import forms
from django.core.exceptions import ValidationError

from apps.schedules.forms import ScheduleAdminForm
from apps.schedules.models import Schedule

Type = Schedule.Type


def _form(cleaned, instance=None):
    """Formulário sem validação de campos; só exercita as regras entre campos."""
    form = ScheduleAdminForm.__new__(ScheduleAdminForm)
    form.cleaned_data = cleaned
    form.instance = instance
    form.add_error = MagicMock()
    return form


def _run_clean(cleaned):
    form = _form(cleaned)
    with patch.object(forms.ModelForm, "clean", return_value=form.cleaned_data):
        form.clean()
    return {call.args[0]: [call.args[1]] for call in form.add_error.call_args_list}


def test_meta():
    assert ScheduleAdminForm.Meta.model is Schedule
    assert ScheduleAdminForm.Meta.fields == (
        "activity",
        "schedule_type",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
    )


def test_weekdays_field():
    field = ScheduleAdminForm.base_fields["weekdays"]
    assert [value for value, _ in field.choices] == [1, 2, 3, 4, 5, 6, 7]
    assert field.required is False
    assert field.widget.__class__ is forms.CheckboxSelectMultiple
    assert field.help_text == (
        "Obrigatório para programações recorrentes. Deve ficar vazio nas pontuais."
    )


def test_recurring_without_days_is_rejected():
    errors = _run_clean({"schedule_type": Type.RECURRING, "weekdays": []})
    assert errors["weekdays"] == ["Selecione ao menos um dia da semana."]


def test_one_time_with_days_is_rejected():
    errors = _run_clean({"schedule_type": Type.ONE_TIME, "weekdays": [2]})
    assert errors["weekdays"] == ["Programação pontual não usa dias da semana."]


def test_valid_combinations_have_no_error():
    assert not _run_clean({"schedule_type": Type.RECURRING, "weekdays": [2, 4]})
    assert not _run_clean({"schedule_type": Type.ONE_TIME, "weekdays": []})


def test_missing_type_adds_no_weekday_error():
    assert not _run_clean({"weekdays": []})


def test_switching_recurring_to_one_time_keeping_days_is_rejected():
    errors = _run_clean({"schedule_type": Type.ONE_TIME, "weekdays": [2, 4]})
    assert "weekdays" in errors


def test_initial_weekdays_come_from_saved_instance():
    instance = MagicMock()
    instance._state.adding = False
    instance.weekdays.values_list.return_value = [2, 4]
    with patch.object(forms.ModelForm, "__init__", lambda self, *a, **k: None):
        form = ScheduleAdminForm.__new__(ScheduleAdminForm)
        form.instance = instance
        form.initial = {}
        ScheduleAdminForm.__init__(form)
    assert form.initial["weekdays"] == [2, 4]


def test_initial_weekdays_empty_for_new_instance():
    instance = SimpleNamespace(_state=SimpleNamespace(adding=True))
    with patch.object(forms.ModelForm, "__init__", lambda self, *a, **k: None):
        form = ScheduleAdminForm.__new__(ScheduleAdminForm)
        form.instance = instance
        form.initial = {}
        ScheduleAdminForm.__init__(form)
    assert "weekdays" not in form.initial


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"end_time": time(14)}, "end_time"),
        ({"start_date": date(2026, 12, 1)}, "end_date"),
    ],
)
def test_model_rules_apply_to_edited_instance(overrides, field):
    values = {
        "schedule_type": Type.RECURRING,
        "start_date": date(2026, 11, 1),
        "end_date": date(2026, 11, 30),
        "start_time": time(14),
        "end_time": time(15),
    }
    values.update(overrides)
    with pytest.raises(ValidationError) as info:
        Schedule(**values).clean()
    assert field in info.value.message_dict
