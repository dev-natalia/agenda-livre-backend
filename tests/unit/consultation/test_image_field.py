import uuid
from datetime import date
from unittest.mock import patch

import pytest
from consultation_helpers import activity, occurrence
from rest_framework.test import APIClient

from apps.activities.models import Activity
from apps.consultation import views
from apps.consultation.serializers import (
    ActivityDetailSerializer,
    ActivityListItemSerializer,
    image_payload,
)

client = APIClient()
PUBLIC_KEYS = {"url", "alt", "decorative"}


def _with_image(
    title="Oficina", alt="Roda de capoeira", decorative=False, name="activities/a.webp"
):
    stored = Activity(image=name).image
    return activity(title, image=stored, image_alt=alt, image_decorative=decorative)


def _list_item(item):
    return ActivityListItemSerializer(instance=(item, None)).data


def _detail(item):
    with patch("apps.consultation.serializers.activity_occurrences", return_value=[]):
        return ActivityDetailSerializer(item).data


@pytest.fixture
def catalog():
    items = []
    with (
        patch.object(views, "published_activities", return_value=items),
        patch("apps.consultation.services.activity_occurrences") as calc,
    ):
        calc.return_value = [occurrence(date(2026, 11, 20))]
        yield items


@pytest.fixture
def detail_source():
    with (
        patch.object(views, "published_activities") as source,
        patch("apps.consultation.serializers.activity_occurrences", return_value=[]),
    ):
        yield source.return_value.prefetch_related.return_value.filter.return_value


# --- image_payload -------------------------------------------------------


def test_payload_is_none_without_image():
    assert image_payload(activity()) is None


def test_payload_has_url_alt_and_decorative_and_nothing_else():
    payload = image_payload(_with_image())

    assert payload == {
        "url": "http://testserver/media/activities/a.webp",
        "alt": "Roda de capoeira",
        "decorative": False,
    }
    assert set(payload) == PUBLIC_KEYS


def test_decorative_payload_has_empty_alt():
    payload = image_payload(_with_image(alt="", decorative=True))

    assert payload["alt"] == ""
    assert payload["decorative"] is True


def test_payload_does_not_expose_the_internal_name_apart_from_the_url():
    payload = image_payload(_with_image(name="activities/segredo123.jpg"))

    assert "name" not in payload and "path" not in payload
    assert payload["url"].endswith("activities/segredo123.jpg")


# --- serializers ---------------------------------------------------------


def test_list_item_without_image_has_the_key_with_none():
    data = _list_item(activity())

    assert "image" in data and data["image"] is None


def test_list_item_with_image():
    assert _list_item(_with_image())["image"]["url"] == "http://testserver/media/activities/a.webp"


def test_detail_without_image_has_the_key_with_none():
    data = _detail(activity())

    assert "image" in data and data["image"] is None


def test_detail_with_image():
    assert _detail(_with_image())["image"] == {
        "url": "http://testserver/media/activities/a.webp",
        "alt": "Roda de capoeira",
        "decorative": False,
    }


def test_existing_list_fields_are_unchanged():
    assert set(_list_item(activity())) == {
        "id",
        "title",
        "slug",
        "summary",
        "unit",
        "category",
        "target_audiences",
        "next_occurrence",
        "image",
    }


def test_existing_detail_fields_are_unchanged():
    assert set(_detail(activity())) == {
        "id",
        "title",
        "slug",
        "summary",
        "description",
        "target_audience_notes",
        "unit",
        "category",
        "target_audiences",
        "external_registration_url",
        "schedules",
        "next_occurrences",
        "image",
    }


# --- endpoints -----------------------------------------------------------


def test_list_endpoint_returns_image_for_every_item(catalog):
    catalog.extend([_with_image("Com imagem"), activity("Sem imagem")])

    results = client.get("/api/v1/activities/").json()["results"]

    by_title = {item["title"]: item for item in results}
    assert by_title["Com imagem"]["image"]["alt"] == "Roda de capoeira"
    assert by_title["Sem imagem"]["image"] is None


def test_detail_endpoint_returns_the_image(detail_source):
    item = _with_image()
    detail_source.first.return_value = item

    body = client.get(f"/api/v1/activities/{item.id}/").json()

    assert body["image"]["url"] == "http://testserver/media/activities/a.webp"


def test_response_has_no_file_path_or_uploader_data(detail_source):
    item = _with_image(name="activities/a.webp")
    detail_source.first.return_value = item

    text = client.get(f"/api/v1/activities/{item.id}/").content.decode()

    assert "created_by" not in text and "updated_by" not in text
    assert "foto original" not in text and "/tmp" not in text and "C:\\" not in text


def test_activity_that_is_not_public_returns_404_without_its_image_url(detail_source):
    detail_source.first.return_value = None  # a consulta só enxerga atividades publicadas

    response = client.get(f"/api/v1/activities/{uuid.uuid4()}/")

    assert response.status_code == 404
    assert response.json() == {"detail": "Não encontrado."}
    assert "media" not in response.content.decode()


def test_public_listing_only_asks_for_published_activities():
    with patch("apps.consultation.services.Activity") as model:
        from apps.consultation.services import published_activities

        published_activities()

    status_filter = model.objects.filter.call_args.kwargs["status__in"]
    assert set(status_filter) == {Activity.Status.PUBLISHED}
