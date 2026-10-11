from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.apps import apps
from django.db.models.signals import post_migrate

from apps.core import permissions
from apps.core.apps import CoreConfig


@pytest.fixture
def orm():
    with (
        patch.object(permissions, "Group") as group_model,
        patch.object(permissions, "Permission") as permission_model,
    ):
        group = MagicMock()
        group_model.objects.using.return_value.get_or_create.return_value = (group, True)
        yield SimpleNamespace(
            group_model=group_model, permission_model=permission_model, group=group
        )


def test_sync_creates_group_with_all_permissions(orm):
    result = permissions.sync_admin_group()

    orm.group_model.objects.using.assert_called_once_with("default")
    orm.group_model.objects.using.return_value.get_or_create.assert_called_once_with(
        name="Administrador"
    )
    all_permissions = orm.permission_model.objects.using.return_value.all.return_value
    orm.group.permissions.set.assert_called_once_with(all_permissions)
    assert result is orm.group


def test_sync_is_idempotent_and_honours_database_alias(orm):
    permissions.sync_admin_group(using="outro")
    permissions.sync_admin_group(using="outro")

    get_or_create = orm.group_model.objects.using.return_value.get_or_create
    assert get_or_create.call_count == 2
    assert orm.group.permissions.set.call_count == 2
    orm.permission_model.objects.using.assert_called_with("outro")


def _user(**overrides):
    values = {"is_authenticated": True, "is_active": True, "is_staff": True}
    values.update(overrides)
    user = SimpleNamespace(**values)
    user.groups = MagicMock()
    user.groups.filter.return_value.exists.return_value = overrides.get("in_group", True)
    return user


def test_admin_account_requires_active_staff_in_group():
    user = _user()

    assert permissions.is_admin_account(user) is True
    user.groups.filter.assert_called_once_with(name="Administrador")


@pytest.mark.parametrize(
    "overrides",
    [
        {"is_authenticated": False},
        {"is_active": False},
        {"is_staff": False},
        {"in_group": False},
    ],
    ids=["anonimo", "inativo", "sem-is-staff", "sem-grupo"],
)
def test_non_admin_accounts_are_rejected(overrides):
    assert permissions.is_admin_account(_user(**overrides)) is False


def test_receiver_syncs_only_after_last_app():
    configs = list(apps.get_app_configs())
    first, last = configs[0], configs[-1]

    with patch.object(permissions, "sync_admin_group") as sync:
        permissions.sync_admin_group_after_migrate(sender=first, using="default")
        sync.assert_not_called()
        permissions.sync_admin_group_after_migrate(sender=last, using="outro")
        sync.assert_called_once_with(using="outro")


def test_ready_connects_receiver_to_post_migrate():
    with patch.object(post_migrate, "connect") as connect:
        CoreConfig.create("apps.core").ready()

    connect.assert_called_once_with(
        permissions.sync_admin_group_after_migrate, dispatch_uid="core.sync_admin_group"
    )
