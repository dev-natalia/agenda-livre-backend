import re

import pytest
from django.core.exceptions import ValidationError

from apps.activities.models import Activity, activity_image_path

MISSING_ALT = "Informe o texto alternativo da imagem ou marque-a como decorativa."
BOTH = "Informe o texto alternativo ou marque a imagem como decorativa, não os dois."


def _activity(**fields):
    base = {"title": "Capoeira", "description": "Aulas", "slug": "capoeira"}
    return Activity(**{**base, **fields})


@pytest.mark.parametrize("filename", ["foto.jpg", "../../etc/passwd.png", "ação final.WEBP"])
def test_upload_path_is_random_and_ignores_the_sent_name(filename):
    path = activity_image_path(None, filename)

    assert re.fullmatch(r"activities/[0-9a-f]{32}\.(jpg|png|webp)", path)
    assert "passwd" not in path and "foto" not in path and "ação" not in path


@pytest.mark.parametrize(
    "filename,extension",
    [("a.jpg", "jpg"), ("a.JPEG", "jpg"), ("a.png", "png"), ("a.WebP", "webp")],
)
def test_upload_path_keeps_an_allowed_extension(filename, extension):
    assert activity_image_path(None, filename).endswith(f".{extension}")


@pytest.mark.parametrize("filename", ["sem-extensao", "script.php", "arquivo.exe", ""])
def test_upload_path_falls_back_to_jpg(filename):
    assert activity_image_path(None, filename).endswith(".jpg")


def test_upload_path_never_repeats():
    paths = {activity_image_path(None, "a.jpg") for _ in range(1000)}

    assert len(paths) == 1000


def test_new_fields_have_safe_defaults():
    activity = _activity()

    assert not activity.image
    assert activity.image_alt == ""
    assert activity.image_decorative is False


def test_image_with_alt_text_is_valid():
    activity = _activity(image="activities/x.jpg", image_alt="  Roda de capoeira  ")

    activity.clean()

    assert activity.image_alt == "Roda de capoeira"
    assert activity.image_decorative is False


def test_decorative_image_is_valid_and_has_no_alt():
    activity = _activity(image="activities/x.jpg", image_decorative=True)

    activity.clean()

    assert activity.image_alt == ""
    assert activity.image_decorative is True


def test_image_without_alt_or_decorative_mark_is_rejected():
    activity = _activity(image="activities/x.jpg")

    with pytest.raises(ValidationError) as error:
        activity.clean()

    assert error.value.message_dict == {"image_alt": [MISSING_ALT]}


def test_alt_with_only_spaces_counts_as_empty():
    activity = _activity(image="activities/x.jpg", image_alt="    ")

    with pytest.raises(ValidationError) as error:
        activity.clean()

    assert error.value.message_dict == {"image_alt": [MISSING_ALT]}


def test_alt_and_decorative_together_are_rejected():
    activity = _activity(image="activities/x.jpg", image_alt="Texto", image_decorative=True)

    with pytest.raises(ValidationError) as error:
        activity.clean()

    assert error.value.message_dict == {"image_decorative": [BOTH]}


def test_without_image_alt_and_decorative_are_cleared_without_error():
    activity = _activity(image_alt="Sobrou do envio anterior", image_decorative=True)

    activity.clean()

    assert activity.image_alt == ""
    assert activity.image_decorative is False


def test_image_errors_are_reported_together_with_other_errors():
    activity = _activity(title="  ", image="activities/x.jpg")

    with pytest.raises(ValidationError) as error:
        activity.clean()

    assert set(error.value.message_dict) == {"title", "image_alt"}


def test_alt_text_is_limited_to_200_characters():
    others = [field.name for field in Activity._meta.fields if field.name != "image_alt"]
    activity = _activity(image="activities/x.jpg", image_alt="a" * 201)

    with pytest.raises(ValidationError) as error:
        activity.clean_fields(exclude=others)

    assert "image_alt" in error.value.message_dict
    activity.image_alt = "a" * 200
    activity.clean_fields(exclude=others)  # não levanta


def test_image_path_is_limited_to_255_characters():
    assert Activity._meta.get_field("image").max_length == 255
