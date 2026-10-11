from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

MODULE = "apps.core.management.commands.safe_migrate"
PASSWORD = "senha-super-secreta"


def _fake_connection():
    connection = MagicMock()
    connection.settings_dict = {
        "HOST": "db.exemplo.local",
        "PORT": 5432,
        "NAME": "agenda",
        "USER": "usuario",
        "PASSWORD": PASSWORD,
    }
    return connection


def _run(answer=None, **options):
    out = StringIO()
    with (
        patch(f"{MODULE}.connection", _fake_connection()),
        patch(f"{MODULE}.call_command") as migrate,
        patch("builtins.input", return_value=answer) as ask,
    ):
        try:
            call_command("safe_migrate", stdout=out, **options)
            error = None
        except CommandError as exc:
            error = exc
    return out.getvalue(), migrate, ask, error


def test_shows_target_without_password_and_migrates_on_confirmation():
    text, migrate, ask, error = _run(answer="s")

    assert error is None
    assert "db.exemplo.local:5432/agenda" in text
    assert "usuario" in text
    assert PASSWORD not in text
    ask.assert_called_once()
    migrate.assert_called_once()
    assert migrate.call_args.args == ("migrate",)


@pytest.mark.parametrize("answer", ["n", "", "sim", "N", "x"])
def test_any_other_answer_cancels_without_migrating(answer):
    _, migrate, _, error = _run(answer=answer)

    assert error is not None
    assert "Nenhuma alteração" in str(error)
    migrate.assert_not_called()


def test_noinput_migrates_without_asking():
    text, migrate, ask, error = _run(interactive=False)

    assert error is None
    assert "db.exemplo.local:5432/agenda" in text
    ask.assert_not_called()
    migrate.assert_called_once()
