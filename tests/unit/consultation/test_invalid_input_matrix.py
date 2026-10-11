import uuid

import pytest

from apps.consultation.serializers import ConsultationQuerySerializer


def _errors(**params):
    serializer = ConsultationQuerySerializer(data=params)
    assert not serializer.is_valid()
    return serializer.errors


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"date": "ontem"}, "date"),
        ({"date": "2026-13-40"}, "date"),
        ({"date_from": "01/02/2026"}, "date_from"),
        ({"date_to": "2026-02-30"}, "date_to"),
        ({"date": "2026-02-01", "date_from": "2026-02-01"}, "date"),
        ({"date_from": "2026-03-02", "date_to": "2026-03-01"}, "date_from"),
        ({"date_from": "2026-01-01", "date_to": "2027-06-01"}, "date_to"),
        ({"unit": "não-é-uuid"}, "unit"),
        ({"category": "123"}, "category"),
        ({"q": "x" * 101}, "q"),
        ({"neighborhood": "x" * 101}, "neighborhood"),
    ],
)
def test_invalid_input_is_rejected_with_portuguese_message_on_the_field(params, field):
    messages = _errors(**params)[field]
    assert messages and all(str(item).endswith(".") for item in messages)
    assert not any(word in str(messages) for word in ("Traceback", "Exception", "None"))


@pytest.mark.parametrize(
    "params",
    [
        {"foo": "bar"},
        {"q": ""},
        {"unit": str(uuid.uuid4()), "extra": "1"},
        {"date": "2026-02-28", "page": "2", "page_size": "5"},
    ],
)
def test_unknown_blank_and_pagination_params_stay_valid(params):
    assert ConsultationQuerySerializer(data=params).is_valid()
