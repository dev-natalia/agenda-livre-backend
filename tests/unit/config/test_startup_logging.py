import logging

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.logging_config import LOG_FILE_NAME, log_startup_failure


@pytest.fixture(autouse=True)
def _reset_logging():
    yield
    for name in ("apps", "config", "django.request"):
        logger = logging.getLogger(name)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


def _content(directory):
    return (directory / LOG_FILE_NAME).read_text(encoding="utf-8")


def test_logs_message_to_file_in_log_dir(clean_env, tmp_path):
    clean_env.setenv("LOG_DIR", str(tmp_path / "meus-logs"))

    log_startup_failure(ImproperlyConfigured("Defina as variáveis de ambiente: DB_HOST"))

    text = _content(tmp_path / "meus-logs")
    assert "ERROR" in text
    assert "DB_HOST" in text


def test_never_raises_when_directory_is_unwritable(clean_env, tmp_path):
    blocker = tmp_path / "arquivo"
    blocker.write_text("x")
    clean_env.setenv("LOG_DIR", str(blocker / "sub"))

    log_startup_failure(ImproperlyConfigured("DB_HOST"))


def test_missing_variable_is_logged_and_reraised(load_settings, clean_env, tmp_path):
    clean_env.setenv("LOG_DIR", str(tmp_path))
    clean_env.delenv("DB_HOST")

    with pytest.raises(ImproperlyConfigured, match="DB_HOST"):
        load_settings()

    text = _content(tmp_path)
    assert "DB_HOST" in text
    assert "senha-super-secreta" not in text
