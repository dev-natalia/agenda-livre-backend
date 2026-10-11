from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.management.commands import create_admin

SECRET = "Senha-Muito-Secreta-123"


@pytest.fixture
def env():
    with (
        patch.object(create_admin, "get_user_model") as get_user_model,
        patch.object(create_admin, "getpass") as getpass,
        patch.object(create_admin, "validate_password") as validate,
        patch.object(create_admin, "sync_admin_group") as sync,
    ):
        user_model = get_user_model.return_value
        user_model.objects.filter.return_value.exists.return_value = False
        getpass.return_value = SECRET
        yield MagicMock(user_model=user_model, getpass=getpass, validate=validate, sync=sync)


def _run(*args):
    out, err = StringIO(), StringIO()
    try:
        call_command("create_admin", *args, stdout=out, stderr=err)
    finally:
        output = out.getvalue() + err.getvalue()
    return output


def test_creates_active_staff_account_in_admin_group(env):
    output = _run("maria")

    env.validate.assert_called_once()
    env.user_model.objects.create_user.assert_called_once_with(
        "maria", password=SECRET, is_staff=True
    )
    user = env.user_model.objects.create_user.return_value
    user.groups.add.assert_called_once_with(env.sync.return_value)
    assert "maria" in output
    assert SECRET not in output


def test_fails_when_username_exists(env):
    env.user_model.objects.filter.return_value.exists.return_value = True

    with pytest.raises(CommandError, match="já existe"):
        _run("maria")

    env.user_model.objects.create_user.assert_not_called()


def test_fails_when_passwords_differ(env):
    env.getpass.side_effect = [SECRET, "outra"]

    with pytest.raises(CommandError, match="não são iguais") as error:
        _run("maria")

    env.user_model.objects.create_user.assert_not_called()
    assert SECRET not in str(error.value)


def test_fails_when_password_is_rejected_by_validators(env):
    env.validate.side_effect = ValidationError(["Senha muito curta."])

    with pytest.raises(CommandError, match="Senha muito curta") as error:
        _run("maria")

    env.user_model.objects.create_user.assert_not_called()
    assert SECRET not in str(error.value)


def test_command_has_no_password_argument():
    parser = create_admin.Command().create_parser("manage.py", "create_admin")
    options = {a.dest for a in parser._actions}

    assert "username" in options
    assert "password" not in options
