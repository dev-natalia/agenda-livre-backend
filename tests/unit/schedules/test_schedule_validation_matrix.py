import pytest
from django import forms

from apps.schedules.forms import ScheduleAdminForm


@pytest.mark.parametrize("value", ["0", "8", "-1", "segunda"])
def test_weekday_outside_monday_to_sunday_is_rejected(value):
    with pytest.raises(forms.ValidationError):
        ScheduleAdminForm.base_fields["weekdays"].clean([value])


@pytest.mark.parametrize("value", ["ANUAL", "", "one_time"])
def test_unknown_schedule_type_is_rejected(value):
    with pytest.raises(forms.ValidationError):
        ScheduleAdminForm.base_fields["schedule_type"].clean(value)
