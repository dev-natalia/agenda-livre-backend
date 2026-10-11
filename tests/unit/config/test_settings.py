import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def test_database_uses_postgresql_with_environment_values(load_settings, valid_env):
    module = load_settings()
    db = module.DATABASES["default"]

    assert db["ENGINE"] == "django.db.backends.postgresql"
    assert db["HOST"] == valid_env["DB_HOST"]
    assert db["PORT"] == 5432
    assert db["NAME"] == valid_env["DB_NAME"]
    assert db["USER"] == valid_env["DB_USER"]
    assert db["PASSWORD"] == valid_env["DB_PASSWORD"]


def test_database_options_have_secure_defaults(load_settings):
    options = load_settings().DATABASES["default"]["OPTIONS"]

    assert options["sslmode"] == "require"
    assert options["connect_timeout"] == 15
    assert "sslrootcert" not in options


def test_database_options_follow_environment(load_settings):
    options = load_settings(DB_SSLMODE="verify-full", DB_SSLROOTCERT="/certs/ca.pem").DATABASES[
        "default"
    ]["OPTIONS"]

    assert options["sslmode"] == "verify-full"
    assert options["sslrootcert"] == "/certs/ca.pem"


def test_application_defaults(load_settings):
    module = load_settings()

    assert module.DEBUG is False
    assert module.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]
    assert module.TIME_ZONE == "America/Sao_Paulo"
    assert module.USE_TZ is True


def test_missing_required_variable_stops_startup(load_settings, clean_env):
    clean_env.delenv("DB_HOST")

    with pytest.raises(ImproperlyConfigured, match="DB_HOST"):
        load_settings()


def test_password_validators_are_enabled():
    names = [v["NAME"].rsplit(".", 1)[-1] for v in settings.AUTH_PASSWORD_VALIDATORS]

    assert names == [
        "UserAttributeSimilarityValidator",
        "MinimumLengthValidator",
        "CommonPasswordValidator",
        "NumericPasswordValidator",
    ]


def test_middleware_order_supports_sessions_auth_and_csrf():
    middleware = [m.rsplit(".", 1)[-1] for m in settings.MIDDLEWARE]

    assert middleware == [
        "SecurityMiddleware",
        "CorsMiddleware",
        "SessionMiddleware",
        "CommonMiddleware",
        "CsrfViewMiddleware",
        "AuthenticationMiddleware",
        "MessageMiddleware",
    ]


def test_passwords_use_django_default_hashing():
    assert settings.PASSWORD_HASHERS[0].endswith("PBKDF2PasswordHasher")


def test_no_login_throttling_is_configured():
    assert settings.AUTHENTICATION_BACKENDS == ["django.contrib.auth.backends.ModelBackend"]
    assert not any("axes" in m.lower() for m in settings.MIDDLEWARE)
