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


def test_logging_defaults(load_settings, tmp_path, clean_env):
    module = load_settings()
    handler = module.LOGGING["handlers"].get("file")

    assert handler["filename"].replace("\\", "/").endswith("/logs/agenda-livre.log")
    assert handler["level"] == "ERROR"
    assert handler["maxBytes"] == 1048576
    assert handler["backupCount"] == 5


def test_logging_follows_environment(load_settings, tmp_path):
    module = load_settings(
        LOG_DIR=str(tmp_path / "x"), LOG_LEVEL="warning", LOG_MAX_BYTES="2048", LOG_BACKUP_COUNT="1"
    )
    handler = module.LOGGING["handlers"]["file"]

    assert handler["filename"].startswith(str(tmp_path / "x"))
    assert handler["level"] == "WARNING"
    assert handler["maxBytes"] == 2048
    assert handler["backupCount"] == 1


@pytest.mark.parametrize(
    "name,value",
    [("LOG_LEVEL", "DEBUG"), ("LOG_MAX_BYTES", "0"), ("LOG_BACKUP_COUNT", "-1")],
)
def test_invalid_log_variables_stop_startup_without_showing_value(load_settings, name, value):
    with pytest.raises(ImproperlyConfigured) as exc:
        load_settings(**{name: value})

    assert name in str(exc.value)
    assert value not in str(exc.value)


def test_secrets_are_passed_to_the_log_formatter(load_settings, valid_env):
    formatter = load_settings().LOGGING["formatters"]["redacting"]

    assert formatter["secrets"] == (valid_env["DJANGO_SECRET_KEY"], valid_env["DB_PASSWORD"])
