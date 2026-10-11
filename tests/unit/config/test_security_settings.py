import pytest
from django.core.exceptions import ImproperlyConfigured

PROTECTIONS = ("SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE")


def _assert_https(module, enabled):
    for name in PROTECTIONS:
        assert getattr(module, name) is enabled
    assert module.SECURE_HSTS_SECONDS == (3600 if enabled else 0)


def test_restrictive_mode_is_default_when_debug_is_off(load_settings):
    _assert_https(load_settings(DJANGO_DEBUG="False"), True)


def test_development_mode_keeps_https_protections_off(load_settings):
    _assert_https(load_settings(DJANGO_DEBUG="True"), False)


def test_https_only_can_be_disabled_for_local_http(load_settings):
    _assert_https(load_settings(DJANGO_DEBUG="False", DJANGO_HTTPS_ONLY="False"), False)


def test_https_only_can_be_forced_in_development(load_settings):
    _assert_https(load_settings(DJANGO_DEBUG="True", DJANGO_HTTPS_ONLY="True"), True)


def test_invalid_https_only_stops_startup(load_settings):
    with pytest.raises(ImproperlyConfigured, match="DJANGO_HTTPS_ONLY"):
        load_settings(DJANGO_HTTPS_ONLY="talvez")


@pytest.mark.parametrize("debug", ["True", "False"])
def test_always_on_protections(load_settings, debug):
    module = load_settings(DJANGO_DEBUG=debug)

    assert module.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert module.X_FRAME_OPTIONS == "DENY"
    assert module.SESSION_COOKIE_HTTPONLY is True
    assert module.SECURE_REFERRER_POLICY == "same-origin"
    assert not hasattr(module, "SECURE_PROXY_SSL_HEADER")
