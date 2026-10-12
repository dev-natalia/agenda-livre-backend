import io
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from PIL import Image

from apps.activities.images import process_image
from apps.activities.models import Activity
from apps.core.management.commands import seed_demo

TITLES = {item["title"] for item in seed_demo.ACTIVITIES}


def _fake_activity(has_image=False):
    activity = MagicMock()
    activity.image.__bool__.return_value = has_image
    activity.title = "Zumba"
    return activity


# --- imagem gerada -------------------------------------------------------


def test_demo_image_is_a_valid_1200_by_800_jpeg():
    image = Image.open(io.BytesIO(seed_demo.build_demo_image("Zumba")))

    assert image.format == "JPEG"
    assert image.size == (1200, 800)


def test_demo_image_passes_the_same_validation_as_real_uploads():
    from django.core.files.uploadedfile import SimpleUploadedFile

    result, extension = process_image(
        SimpleUploadedFile("demo.jpg", seed_demo.build_demo_image("Zumba"))
    )

    assert extension == "jpg"
    assert result.size > 0


def test_demo_image_is_deterministic_per_seed():
    assert seed_demo.build_demo_image("A") == seed_demo.build_demo_image("A")
    assert seed_demo.build_demo_image("A") != seed_demo.build_demo_image("B")


def test_demo_image_has_no_metadata():
    image = Image.open(io.BytesIO(seed_demo.build_demo_image("Zumba")))

    assert len(image.getexif()) == 0


# --- plano de imagens ----------------------------------------------------


def test_plan_only_names_existing_demo_activities():
    assert set(seed_demo.IMAGE_PLAN) <= TITLES


def test_about_two_thirds_of_the_activities_get_an_image():
    share = len(seed_demo.IMAGE_PLAN) / len(seed_demo.ACTIVITIES)

    assert 0.5 <= share <= 0.8


def test_some_images_are_decorative_and_some_published_activities_have_none():
    decorative = [plan for plan in seed_demo.IMAGE_PLAN.values() if plan.get("decorative")]
    published_without = [
        item
        for item in seed_demo.ACTIVITIES
        if item["status"] == seed_demo.PUBLISHED and item["title"] not in seed_demo.IMAGE_PLAN
    ]

    assert decorative
    assert published_without


def test_every_image_has_alt_text_or_is_decorative_never_both():
    for title, plan in seed_demo.IMAGE_PLAN.items():
        alt, decorative = plan.get("alt", ""), plan.get("decorative", False)
        assert bool(alt.strip()) != decorative, title
        assert len(alt) <= 200, title


def test_alt_texts_say_the_image_is_fictional_and_mention_no_brand_or_person():
    for plan in seed_demo.IMAGE_PLAN.values():
        alt = plan.get("alt")
        if alt:
            assert "fictícia" in alt
            assert not any(word in alt.lower() for word in ("pessoa", "foto", "logo", "marca"))


# --- anexar a imagem -----------------------------------------------------


def test_attach_saves_the_processed_image_and_the_accessibility_fields():
    activity = _fake_activity()

    attached = seed_demo._attach_image(activity, {"alt": "Texto alternativo"})

    assert attached is True
    name, content = activity.image.save.call_args.args
    assert name == "demo.jpg" and content.size > 0
    assert activity.image.save.call_args.kwargs == {"save": False}
    assert activity.image_alt == "Texto alternativo"
    assert activity.image_decorative is False
    activity.save.assert_called_once_with(
        update_fields=["image", "image_alt", "image_decorative", "updated_at"]
    )


def test_attach_decorative_image_has_no_alt():
    activity = _fake_activity()

    seed_demo._attach_image(activity, {"decorative": True})

    assert activity.image_alt == ""
    assert activity.image_decorative is True


def test_attach_does_nothing_when_the_activity_already_has_an_image():
    activity = Activity(image="activities/atual.jpg")
    activity.save = MagicMock()

    assert seed_demo._attach_image(activity, {"alt": "x"}) is False
    activity.save.assert_not_called()


# --- passo no comando ----------------------------------------------------


def _units():
    return {item["unit"]: f"unidade-{item['unit']}" for item in seed_demo.ACTIVITIES}


def test_attach_demo_images_runs_for_existing_activities_and_counts():
    found = _fake_activity()
    with (
        patch.object(seed_demo.Activity, "objects") as activities,
        patch.object(seed_demo, "_attach_image", side_effect=[True, False] * 10) as attach,
    ):
        activities.filter.return_value.first.return_value = found
        attached, existing = seed_demo._attach_demo_images(_units())

    assert attach.call_count == len(seed_demo.IMAGE_PLAN)
    assert (attached, existing) == (5, 5)


def test_attach_demo_images_skips_activities_that_do_not_exist_yet():
    with (
        patch.object(seed_demo.Activity, "objects") as activities,
        patch.object(seed_demo, "_attach_image") as attach,
    ):
        activities.filter.return_value.first.return_value = None
        assert seed_demo._attach_demo_images(_units()) == (0, 0)

    attach.assert_not_called()


def test_attach_demo_images_skips_activities_without_a_plan():
    with (
        patch.object(seed_demo.Activity, "objects") as activities,
        patch.object(seed_demo, "_attach_image", return_value=True),
    ):
        activities.filter.return_value.first.return_value = _fake_activity()
        seed_demo._attach_demo_images(_units())

    queried = {call.kwargs["title"] for call in activities.filter.call_args_list}
    assert queried == set(seed_demo.IMAGE_PLAN)


def _run(attach):
    out = StringIO()
    with (
        patch.object(seed_demo, "_admin_user", return_value="admin"),
        patch.object(seed_demo, "_load", return_value=(0, 3)),
        patch.object(seed_demo, "_by_slug", return_value=MagicMock()),
        patch.object(seed_demo.Activity, "objects") as activities,
        patch.object(seed_demo, "_create_activity"),
        patch.object(seed_demo, "_attach_demo_images", **attach),
        patch.object(seed_demo.transaction, "atomic"),
    ):
        activities.filter.return_value.exists.return_value = True
        call_command("seed_demo", stdout=out)
    return out.getvalue()


def test_command_runs_the_image_step_even_when_the_activities_already_exist():
    output = _run({"return_value": (4, 6)})

    assert "Imagens: 4 anexada(s), 6 já existiam." in output


def test_command_reports_a_storage_failure_without_details():
    with pytest.raises(CommandError) as error:
        _run({"side_effect": RuntimeError("AccessDenied segredo")})

    assert "RuntimeError" in str(error.value)
    assert "segredo" not in str(error.value)
    assert "AWS_*" in str(error.value)
