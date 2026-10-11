import re
from pathlib import Path

import pytest
from rest_framework.exceptions import ValidationError

from apps.core.exceptions import UNEXPECTED_ERROR_MESSAGE, public_exception_handler

ROOT = Path(__file__).resolve().parents[3]
SOURCES = [
    ROOT / "apps" / "consultation" / "serializers.py",
    ROOT / "apps" / "consultation" / "pagination.py",
    ROOT / "apps" / "core" / "exceptions.py",
]
TECHNICAL = ("Traceback", "Exception", "None", "NoneType", "KeyError", "SELECT ")


def _user_messages():
    pattern = re.compile(r'"((?:Informe|Use|A |O |Ocorreu|Parâmetros|Não)[^"]*\.)"')
    found = []
    for source in SOURCES:
        found += pattern.findall(source.read_text(encoding="utf-8"))
    return found


def test_there_are_messages_to_check():
    assert len(_user_messages()) >= 6


@pytest.mark.parametrize("message", _user_messages())
def test_messages_are_plain_portuguese_without_technical_terms(message):
    assert message.endswith(".")
    assert not any(term in message for term in TECHNICAL)


def test_unexpected_error_message_is_plain_and_actionable():
    assert "tente novamente" in UNEXPECTED_ERROR_MESSAGE.lower()


def test_field_errors_name_the_field_and_fieldless_errors_use_non_field_errors():
    named = public_exception_handler(ValidationError({"unit": ["Inválido."]}), {}).data
    assert list(named["errors"]) == ["unit"]
    fieldless = public_exception_handler(ValidationError("Algo está errado."), {}).data
    assert list(fieldless["errors"]) == ["non_field_errors"]
