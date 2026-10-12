from unittest.mock import patch

import pytest
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.activities.forms import ActivityAdminForm
from apps.activities.models import Activity


def _form(image):
    form = ActivityAdminForm()
    form.cleaned_data = {"image": image}
    return form


def test_form_is_for_activity_and_exposes_the_image_fields():
    form = ActivityAdminForm()

    assert ActivityAdminForm._meta.model is Activity
    assert {"image", "image_alt", "image_decorative"} <= set(form.fields)


def test_image_is_optional_and_can_be_cleared():
    field = ActivityAdminForm().fields["image"]

    assert field.required is False
    assert isinstance(field.widget, forms.ClearableFileInput)


def test_only_process_image_validates_the_file_so_messages_are_ours():
    field = ActivityAdminForm().fields["image"]

    assert type(field) is forms.FileField
    assert not isinstance(field, forms.ImageField)


def test_new_upload_is_processed_and_renamed():
    upload = SimpleUploadedFile("foto original.png", b"bytes")
    processed = ContentFile(b"tratado")

    with patch("apps.activities.forms.process_image", return_value=(processed, "webp")) as run:
        result = _form(upload).clean_image()

    run.assert_called_once_with(upload)
    assert result.name == "imagem.webp"
    assert result.read() == b"tratado"


def test_upload_error_is_reported_on_the_image_field():
    upload = SimpleUploadedFile("a.jpg", b"nada")

    with patch(
        "apps.activities.forms.process_image",
        side_effect=ValidationError("Envie uma imagem JPEG, PNG ou WebP."),
    ):
        with pytest.raises(ValidationError) as error:
            _form(upload).clean_image()

    assert error.value.messages == ["Envie uma imagem JPEG, PNG ou WebP."]


@pytest.mark.parametrize("value", [None, False, ""])
def test_no_new_file_is_not_processed(value):
    with patch("apps.activities.forms.process_image") as run:
        result = _form(value).clean_image()

    run.assert_not_called()
    assert result == value


def test_current_file_is_not_processed_again():
    current = Activity(image="activities/atual.jpg").image

    with patch("apps.activities.forms.process_image") as run:
        result = _form(current).clean_image()

    run.assert_not_called()
    assert result is current
