from django.conf import settings
from django.test import override_settings
from rest_framework.test import APIClient

ALLOWED_ORIGIN = "http://localhost:5500"
OTHER_ORIGIN = "http://outro.exemplo"


def _get_health(origin):
    return APIClient().get("/api/v1/health/", HTTP_ORIGIN=origin)


def test_cors_middleware_is_enabled_before_common_middleware():
    middleware = settings.MIDDLEWARE

    assert "corsheaders" in settings.INSTALLED_APPS
    assert middleware.index("corsheaders.middleware.CorsMiddleware") < middleware.index(
        "django.middleware.common.CommonMiddleware"
    )


@override_settings(CORS_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
def test_allowed_origin_receives_cors_header():
    response = _get_health(ALLOWED_ORIGIN)

    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN


@override_settings(CORS_ALLOWED_ORIGINS=[ALLOWED_ORIGIN])
def test_unlisted_origin_does_not_receive_cors_header():
    response = _get_health(OTHER_ORIGIN)

    assert "Access-Control-Allow-Origin" not in response


@override_settings(CORS_ALLOWED_ORIGINS=[])
def test_empty_list_authorizes_nobody():
    response = _get_health(ALLOWED_ORIGIN)

    assert "Access-Control-Allow-Origin" not in response


def test_origins_default_to_empty_list(load_settings):
    assert load_settings().CORS_ALLOWED_ORIGINS == []


def test_origins_are_read_from_comma_separated_variable(load_settings):
    module = load_settings(CORS_ALLOWED_ORIGINS="http://a.local:5500, http://b.local:3000")

    assert module.CORS_ALLOWED_ORIGINS == ["http://a.local:5500", "http://b.local:3000"]
