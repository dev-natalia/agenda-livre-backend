from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.utils import OperationalError

TARGET = "apps.core.management.commands.check_db.connection"
PASSWORD = "senha-super-secreta"


def _fake_connection(error=None):
    connection = MagicMock()
    connection.settings_dict = {
        "HOST": "db.exemplo.local",
        "PORT": 5432,
        "NAME": "agenda",
        "USER": "usuario",
        "PASSWORD": PASSWORD,
    }
    if error is not None:
        connection.cursor.side_effect = error
    return connection


def test_reports_success_with_target_without_password():
    out = StringIO()

    with patch(TARGET, _fake_connection()):
        call_command("check_db", stdout=out)

    text = out.getvalue()
    assert "db.exemplo.local:5432/agenda" in text
    assert "funcionou" in text
    assert PASSWORD not in text


@pytest.mark.parametrize(
    "raw_error,expected",
    [
        ('FATAL: password authentication failed for user "usuario"', "credenciais recusadas"),
        ("connection timeout expired", "tempo esgotado"),
        ("could not translate host name", "host não encontrado"),
        ("connection refused", "conexão recusada"),
        ('database "agenda" does not exist', "banco inexistente"),
        ("SSL connection is required", "falha de TLS"),
        ("algo inesperado", "falha de conexão"),
    ],
)
def test_reports_failure_type_and_exits_with_error(raw_error, expected):
    with patch(TARGET, _fake_connection(OperationalError(raw_error))):
        with pytest.raises(CommandError) as exc:
            call_command("check_db", stdout=StringIO())

    message = str(exc.value)
    assert expected in message
    assert "db.exemplo.local:5432/agenda" in message
    assert PASSWORD not in message


def test_failure_does_not_echo_raw_driver_message():
    error = OperationalError(f"detalhe interno com {PASSWORD}")

    with patch(TARGET, _fake_connection(error)):
        with pytest.raises(CommandError) as exc:
            call_command("check_db", stdout=StringIO())

    assert PASSWORD not in str(exc.value)
