import logging
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.apps import apps as django_apps
from django.contrib import admin
from django.db.models.signals import post_delete
from django.test import RequestFactory

from apps.activities import signals
from apps.activities.admin import ActivityAdmin
from apps.activities.images import delete_stored_file
from apps.activities.models import Activity
from config.logging_config import RedactingFormatter

SECRET = "chave-secreta-aws-de-teste"


def _run_now(callback):
    callback()


@pytest.fixture
def storage():
    with patch("apps.activities.images.default_storage") as mocked:
        yield mocked


@pytest.fixture
def model_admin():
    return ActivityAdmin(Activity, admin.site)


def _request():
    request = RequestFactory().post("/")
    request.user = SimpleNamespace(pk=1)
    return request


# --- delete_stored_file --------------------------------------------------


def test_delete_stored_file_removes_the_object(storage):
    delete_stored_file("activities/a.jpg")

    storage.delete.assert_called_once_with("activities/a.jpg")


@pytest.mark.parametrize("name", ["", None])
def test_delete_stored_file_ignores_an_empty_name(storage, name):
    delete_stored_file(name)

    storage.delete.assert_not_called()


def test_delete_failure_is_logged_and_never_raised(storage, caplog):
    storage.delete.side_effect = RuntimeError(f"AccessDenied {SECRET}")

    with caplog.at_level(logging.ERROR):
        delete_stored_file("activities/a.jpg")

    assert "activities/a.jpg" in caplog.text
    assert "RuntimeError" in caplog.text
    assert SECRET not in caplog.text


def test_failure_log_is_masked_by_the_configured_formatter(storage, caplog):
    storage.delete.side_effect = RuntimeError("falhou")
    with caplog.at_level(logging.ERROR):
        delete_stored_file("activities/a.jpg")

    formatter = RedactingFormatter(secrets=(SECRET,))
    record = caplog.records[-1]
    record.msg = f"{record.getMessage()} {SECRET}"
    record.args = ()

    assert SECRET not in formatter.format(record)


# --- exclusão da atividade ----------------------------------------------


def test_deleting_an_activity_schedules_the_removal_of_its_file():
    instance = Activity(image="activities/a.jpg")

    with (
        patch("apps.activities.signals.transaction.on_commit", side_effect=_run_now),
        patch("apps.activities.signals.delete_stored_file") as remove,
    ):
        signals.delete_image_file(sender=Activity, instance=instance)

    remove.assert_called_once_with("activities/a.jpg")


def test_deleting_an_activity_without_image_does_nothing():
    with (
        patch("apps.activities.signals.transaction.on_commit") as on_commit,
        patch("apps.activities.signals.delete_stored_file") as remove,
    ):
        signals.delete_image_file(sender=Activity, instance=Activity())

    on_commit.assert_not_called()
    remove.assert_not_called()


def test_removal_waits_for_the_commit():
    callbacks = []

    with (
        patch("apps.activities.signals.transaction.on_commit", side_effect=callbacks.append),
        patch("apps.activities.signals.delete_stored_file") as remove,
    ):
        signals.delete_image_file(sender=Activity, instance=Activity(image="activities/a.jpg"))
        remove.assert_not_called()
        callbacks[0]()

    remove.assert_called_once_with("activities/a.jpg")


def test_signal_is_registered_for_activity():
    assert post_delete.has_listeners(Activity)


# --- troca e remoção pelo Admin -----------------------------------------


def _save(model_admin, form, change=True):
    with (
        patch.object(admin.ModelAdmin, "save_model"),
        patch("apps.activities.admin.transaction.on_commit", side_effect=_run_now),
        patch("apps.activities.admin.delete_stored_file") as remove,
    ):
        model_admin.save_model(_request(), SimpleNamespace(), form, change=change)
    return remove


def test_replacing_the_image_removes_the_old_file(model_admin):
    old = Activity(image="activities/antiga.jpg").image
    form = SimpleNamespace(changed_data=["image"], initial={"image": old})

    _save(model_admin, form).assert_called_once_with("activities/antiga.jpg")


def test_clearing_the_image_removes_the_old_file(model_admin):
    old = Activity(image="activities/antiga.jpg").image
    form = SimpleNamespace(changed_data=["image", "image_alt"], initial={"image": old})

    _save(model_admin, form).assert_called_once_with("activities/antiga.jpg")


def test_old_file_can_be_given_as_a_plain_name(model_admin):
    form = SimpleNamespace(changed_data=["image"], initial={"image": "activities/antiga.jpg"})

    _save(model_admin, form).assert_called_once_with("activities/antiga.jpg")


def test_changing_only_the_alt_text_keeps_the_file(model_admin):
    old = Activity(image="activities/antiga.jpg").image
    form = SimpleNamespace(changed_data=["image_alt"], initial={"image": old})

    _save(model_admin, form).assert_not_called()


def test_first_image_of_an_activity_has_nothing_to_remove(model_admin):
    form = SimpleNamespace(changed_data=["image"], initial={"image": None})

    _save(model_admin, form, change=False).assert_not_called()


def test_removal_after_the_admin_save_waits_for_the_commit(model_admin):
    old = Activity(image="activities/antiga.jpg").image
    form = SimpleNamespace(changed_data=["image"], initial={"image": old})
    callbacks = []

    with (
        patch.object(admin.ModelAdmin, "save_model"),
        patch("apps.activities.admin.transaction.on_commit", side_effect=callbacks.append),
        patch("apps.activities.admin.delete_stored_file") as remove,
    ):
        model_admin.save_model(_request(), SimpleNamespace(), form, change=True)
        remove.assert_not_called()
        callbacks[0]()

    remove.assert_called_once_with("activities/antiga.jpg")


def test_app_config_registers_the_signals():
    config = django_apps.get_app_config("activities")

    with patch("apps.activities.apps.importlib.import_module") as load:
        config.ready()

    load.assert_called_once_with("apps.activities.signals")
