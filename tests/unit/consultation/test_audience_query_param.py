import uuid

import pytest
from django.http import QueryDict

from apps.consultation.serializers import ConsultationQuerySerializer
from apps.consultation.services import Criteria

MESSAGE = "Informe um identificador válido."


def _serializer(**params):
    query = QueryDict(mutable=True)
    query.update(params)
    return ConsultationQuerySerializer(data=query)


def _criteria(**params):
    serializer = _serializer(**params)
    assert serializer.is_valid(), serializer.errors
    return serializer.criteria()


def _errors(**params):
    serializer = _serializer(**params)
    assert not serializer.is_valid()
    return serializer.errors


def test_criteria_has_an_audience_field_defaulting_to_none():
    assert Criteria().audience is None


def test_valid_audience_reaches_the_criteria_as_a_uuid():
    wanted = uuid.uuid4()

    assert _criteria(audience=str(wanted)).audience == wanted


def test_missing_audience_is_none():
    assert _criteria().audience is None


@pytest.mark.parametrize("value", ["abc", "123", "0000"])
def test_invalid_audience_is_reported_on_its_field(value):
    errors = _errors(audience=value)

    assert {key: [str(message) for message in found] for key, found in errors.items()} == {
        "audience": [MESSAGE]
    }


def test_empty_audience_is_treated_as_absent_like_unit_and_category():
    assert _criteria(audience="").audience is None
    assert _criteria(unit="").unit is None


def test_repeated_audience_uses_the_last_value():
    first, last = uuid.uuid4(), uuid.uuid4()
    query = QueryDict(f"audience={first}&audience={last}")
    serializer = ConsultationQuerySerializer(data=query)

    assert serializer.is_valid()
    assert serializer.criteria().audience == last


def test_audience_is_accepted_together_with_every_other_filter():
    unit, category, wanted = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    criteria = _criteria(
        audience=str(wanted),
        unit=str(unit),
        category=str(category),
        q="danca",
        neighborhood="Grajaú",
        date_from="2026-11-01",
        date_to="2026-11-30",
    )

    assert criteria.audience == wanted
    assert (criteria.unit, criteria.category) == (unit, category)
    assert (criteria.q, criteria.neighborhood) == ("danca", "Grajaú")
    assert str(criteria.date_from) == "2026-11-01" and str(criteria.date_to) == "2026-11-30"


def test_single_date_with_audience_fills_both_ends():
    criteria = _criteria(audience=str(uuid.uuid4()), date="2026-11-01")

    assert criteria.date_from == criteria.date_to


def test_date_with_a_range_is_still_refused_when_audience_is_present():
    errors = _errors(audience=str(uuid.uuid4()), date="2026-11-01", date_from="2026-11-01")

    assert set(errors) == {"date"}


def test_several_errors_are_reported_each_on_its_own_field():
    errors = _errors(audience="abc", unit="x", date_from="2026-13-40")

    assert set(errors) == {"audience", "unit", "date_from"}
