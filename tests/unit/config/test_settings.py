import pytest
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
