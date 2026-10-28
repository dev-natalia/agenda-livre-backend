from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponseRedirect
from django.test import RequestFactory
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from apps.activities.admin import ActivityAdmin
from apps.activities.forms import ActivityAdminForm
from apps.activities.models import Activity

FAILURE_MESSAGE = "Não foi possível guardar a imagem agora. Tente novamente."


@pytest.fixture
def model_admin():
    instance = ActivityAdmin(Activity, admin.site)
    instance.message_user = MagicMock()
    return instance


def _post(with_image=True):
    files = {"image": SimpleUploadedFile("a.jpg", b"x")} if with_image else {}
    request = RequestFactory().post("/admin/activities/activity/add/", files)
    request.user = SimpleNamespace(pk=1)
    return request


def _client_error():
    return ClientError({"Error": {"Code": "AccessDenied", "Message": "segredo"}}, "PutObject")


def test_admin_uses_the_activity_form(model_admin):
    assert model_admin.form is ActivityAdminForm


def test_image_fields_come_after_the_link_and_before_the_status(model_admin):
    fields = list(model_admin.fields)

    assert fields[fields.index("external_registration_url") + 1 : fields.index("status")] == [
        "image",
        "image_preview",
        "image_alt",
        "image_decorative",
    ]
    assert "image_preview" in model_admin.readonly_fields


def test_preview_shows_the_current_image_with_its_alt_text(model_admin):
    activity = Activity(image="activities/x.jpg", image_alt='Roda "de" capoeira')

    html = model_admin.image_preview(activity)

    assert "<img" in html and "max-width" in html
    assert 'alt="Roda &quot;de&quot; capoeira"' in html
    assert "activities/x.jpg" in html


def test_preview_of_decorative_image_has_empty_alt(model_admin):
    activity = Activity(image="activities/x.jpg", image_decorative=True)

    assert 'alt=""' in model_admin.image_preview(activity)


@pytest.mark.parametrize("obj", [None, Activity(), Activity(image="")])
def test_preview_without_image(model_admin, obj):
    assert model_admin.image_preview(obj) == "Sem imagem."


def test_storage_failure_redirects_back_with_a_generic_message(model_admin, caplog):
    request = _post()

    with patch.object(UnfoldModelAdmin, "changeform_view", side_effect=_client_error()):
        response = model_admin.changeform_view(request)

    assert isinstance(response, HttpResponseRedirect)
    assert response.url == request.get_full_path()
    model_admin.message_user.assert_called_once_with(request, FAILURE_MESSAGE, messages.ERROR)
    assert "ClientError" in caplog.text
    assert "segredo" not in caplog.text and "AccessDenied" not in caplog.text


def test_os_error_is_treated_the_same_way(model_admin):
    with patch.object(UnfoldModelAdmin, "changeform_view", side_effect=OSError("disco")):
        response = model_admin.changeform_view(_post())

    assert isinstance(response, HttpResponseRedirect)


def test_failure_without_an_uploaded_image_propagates(model_admin):
    with patch.object(UnfoldModelAdmin, "changeform_view", side_effect=_client_error()):
        with pytest.raises(ClientError):
            model_admin.changeform_view(_post(with_image=False))


def test_failure_on_a_get_request_propagates(model_admin):
    request = RequestFactory().get("/admin/activities/activity/add/")

    with patch.object(UnfoldModelAdmin, "changeform_view", side_effect=_client_error()):
        with pytest.raises(ClientError):
            model_admin.changeform_view(request)


@pytest.mark.parametrize("error", [ValidationError("x"), PermissionDenied(), Http404()])
def test_expected_errors_are_not_swallowed(model_admin, error):
    with patch.object(UnfoldModelAdmin, "changeform_view", side_effect=error):
        with pytest.raises(type(error)):
            model_admin.changeform_view(_post())


def test_successful_save_returns_the_parent_response(model_admin):
    with patch.object(UnfoldModelAdmin, "changeform_view", return_value="ok") as parent:
        assert model_admin.changeform_view(_post(), "1", "/u/", {"a": 1}) == "ok"

    parent.assert_called_once()


@pytest.mark.parametrize("changed", [["image"], ["image", "image_alt"]])
def test_replacing_or_clearing_the_image_updates_the_audit_fields(model_admin, changed):
    request = _post()
    obj = SimpleNamespace(created_by=object())
    form = SimpleNamespace(changed_data=changed, initial={})

    with patch.object(UnfoldModelAdmin, "save_model") as parent:
        model_admin.save_model(request, obj, form, change=True)

    assert obj.updated_by is request.user
    parent.assert_called_once()
