import logging
import logging.config
import logging.handlers
from unittest.mock import patch

import pytest

from config.logging_config import LOG_FILE_NAME, build_logging

SECRETS = ("chave-secreta-de-teste-123", "senha-do-banco-456")
LOGGER_NAMES = ("apps", "config", "django.request")


@pytest.fixture(autouse=True)
def _reset_logging():
    yield
    for name in LOGGER_NAMES:
        logger = logging.getLogger(name)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


def _build(tmp_path, level="ERROR", max_bytes=1024, backup_count=2):
    return build_logging(tmp_path / "logs", level, max_bytes, backup_count, SECRETS)


def test_config_is_accepted_by_dict_config(tmp_path):
    config = _build(tmp_path)

    logging.config.dictConfig(config)

    assert config["disable_existing_loggers"] is False
    assert logging.getLogger("apps").handlers


def test_file_handler_is_rotating_with_given_limits(tmp_path):
    handler = _build(tmp_path, max_bytes=2048, backup_count=3)["handlers"]["file"]

    assert handler["class"] == "logging.handlers.RotatingFileHandler"
    assert handler["filename"] == str(tmp_path / "logs" / LOG_FILE_NAME)
    assert LOG_FILE_NAME == "agenda-livre.log"
    assert handler["maxBytes"] == 2048
    assert handler["backupCount"] == 3
    assert handler["delay"] is True
    assert handler["encoding"] == "utf-8"
    assert handler["level"] == "ERROR"
    assert handler["formatter"] == "redacting"


def test_level_comes_from_parameter(tmp_path):
    assert _build(tmp_path, level="CRITICAL")["handlers"]["file"]["level"] == "CRITICAL"


def test_loggers_use_the_file(tmp_path):
    loggers = _build(tmp_path)["loggers"]

    for name in LOGGER_NAMES:
        assert "file" in loggers[name]["handlers"]


def test_formatter_receives_the_secrets(tmp_path):
    formatter = _build(tmp_path)["formatters"]["redacting"]

    assert formatter["secrets"] == SECRETS


def test_writes_only_errors_and_masks_secret(tmp_path):
    logging.config.dictConfig(_build(tmp_path))
    logger = logging.getLogger("apps.teste")

    logger.warning("aviso comum")
    logger.error("falha com %s", SECRETS[1])
    for handler in logging.getLogger("apps").handlers:
        handler.flush()

    content = (tmp_path / "logs" / LOG_FILE_NAME).read_text(encoding="utf-8")
    assert "aviso comum" not in content
    assert "falha com ***" in content
    assert SECRETS[1] not in content


def test_rotation_keeps_total_size_within_limit(tmp_path):
    max_bytes, backups = 400, 2
    logging.config.dictConfig(_build(tmp_path, max_bytes=max_bytes, backup_count=backups))
    logger = logging.getLogger("apps.rotacao")

    for number in range(200):
        logger.error("ocorrencia numero %s com texto de preenchimento", number)

    files = list((tmp_path / "logs").iterdir())
    assert len(files) <= backups + 1
    assert sum(item.stat().st_size for item in files) <= max_bytes * (backups + 1)


def test_unwritable_directory_falls_back_to_console(tmp_path, capsys):
    with patch("config.logging_config.os.makedirs", side_effect=OSError("sem permissão")):
        config = _build(tmp_path)

    assert "file" not in config["handlers"]
    assert "console" in config["handlers"]
    for name in LOGGER_NAMES:
        assert config["loggers"][name]["handlers"] == ["console"]
    assert "registro de erros em arquivo desativado" in capsys.readouterr().err.lower()
    logging.config.dictConfig(config)


def test_emit_failure_does_not_propagate(tmp_path):
    logging.config.dictConfig(_build(tmp_path))

    with patch.object(logging.handlers.RotatingFileHandler, "_open", side_effect=OSError("disco")):
        with patch.object(logging, "raiseExceptions", False):
            logging.getLogger("apps.falha").error("não deve levantar")
