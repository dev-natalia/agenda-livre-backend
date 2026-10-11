from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from config import env


def _set_all(monkeypatch, values):
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_require_env_returns_values(clean_env, valid_env):
    _set_all(clean_env, valid_env)

    assert env.require_env(env.REQUIRED_VARS) == valid_env


def test_require_env_lists_all_missing_in_one_message(clean_env, valid_env):
    valid_env.pop("DB_HOST")
    valid_env.pop("DB_PASSWORD")
    _set_all(clean_env, valid_env)

    with pytest.raises(ImproperlyConfigured) as exc:
        env.require_env(env.REQUIRED_VARS)

    assert str(exc.value) == (
        "Configuração incompleta. Defina as variáveis de ambiente: DB_HOST, DB_PASSWORD"
    )


def test_require_env_treats_blank_value_as_missing(clean_env, valid_env):
    valid_env["DB_NAME"] = "   "
    _set_all(clean_env, valid_env)

    with pytest.raises(ImproperlyConfigured, match="DB_NAME"):
        env.require_env(env.REQUIRED_VARS)


def test_require_env_error_never_contains_values(clean_env, valid_env):
    valid_env.pop("DB_HOST")
    _set_all(clean_env, valid_env)

    with pytest.raises(ImproperlyConfigured) as exc:
        env.require_env(env.REQUIRED_VARS)

    message = str(exc.value)
    assert valid_env["DB_PASSWORD"] not in message
    assert valid_env["DJANGO_SECRET_KEY"] not in message


@pytest.mark.parametrize("value", ["abc", "", "5432.5", "0", "65536", "-1"])
def test_parse_port_rejects_invalid_values(value):
    with pytest.raises(ImproperlyConfigured, match="DB_PORT"):
        env.parse_port(value)


@pytest.mark.parametrize("value,expected", [("1", 1), ("5432", 5432), ("65535", 65535)])
def test_parse_port_accepts_valid_values(value, expected):
    assert env.parse_port(value) == expected


def test_get_bool_defaults_to_false(clean_env):
    assert env.get_bool("DJANGO_DEBUG") is False


@pytest.mark.parametrize("raw", ["True", "true", "1", "yes"])
def test_get_bool_true_values(clean_env, raw):
    clean_env.setenv("DJANGO_DEBUG", raw)

    assert env.get_bool("DJANGO_DEBUG") is True


@pytest.mark.parametrize("raw", ["False", "false", "0", "no"])
def test_get_bool_false_values(clean_env, raw):
    clean_env.setenv("DJANGO_DEBUG", raw)

    assert env.get_bool("DJANGO_DEBUG", default=True) is False


def test_get_bool_rejects_other_values(clean_env):
    clean_env.setenv("DJANGO_DEBUG", "talvez")

    with pytest.raises(ImproperlyConfigured, match="DJANGO_DEBUG"):
        env.get_bool("DJANGO_DEBUG")


def test_ssl_mode_defaults_to_require(clean_env):
    assert env.get_ssl_mode() == "require"


@pytest.mark.parametrize("mode", env.SSL_MODES)
def test_ssl_mode_accepts_postgres_modes(clean_env, mode):
    clean_env.setenv("DB_SSLMODE", mode)

    assert env.get_ssl_mode() == mode


def test_ssl_mode_rejects_invalid_value(clean_env):
    clean_env.setenv("DB_SSLMODE", "inventado")

    with pytest.raises(ImproperlyConfigured, match="DB_SSLMODE"):
        env.get_ssl_mode()


def test_get_list_uses_default_and_strips_items(clean_env):
    assert env.get_list("CORS_ALLOWED_ORIGINS") == []
    assert env.get_list("DJANGO_ALLOWED_HOSTS", "a, b ,,c") == ["a", "b", "c"]


def test_get_list_reads_environment(clean_env):
    clean_env.setenv("CORS_ALLOWED_ORIGINS", "http://x.local, http://y.local")

    assert env.get_list("CORS_ALLOWED_ORIGINS") == ["http://x.local", "http://y.local"]


def test_load_dotenv_reads_file_from_base_dir():
    with patch("config.env.environ.Env.read_env") as read_env:
        env.load_dotenv()

    read_env.assert_called_once_with(env.BASE_DIR / ".env")
