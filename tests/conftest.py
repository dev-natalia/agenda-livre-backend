import importlib

import pytest

import config.settings
from config.env import ALL_VARS


@pytest.fixture
def valid_env():
    """Variáveis obrigatórias com valores válidos (fictícios)."""
    return {
        "DJANGO_SECRET_KEY": "segredo-de-teste",
        "DB_HOST": "db.exemplo.local",
        "DB_PORT": "5432",
        "DB_NAME": "agenda",
        "DB_USER": "usuario",
        "DB_PASSWORD": "senha-super-secreta",
        "AWS_ACCESS_KEY_ID": "chave-de-acesso-aws",
        "AWS_SECRET_ACCESS_KEY": "chave-secreta-aws",
        "AWS_STORAGE_BUCKET_NAME": "bucket-de-teste",
        "AWS_S3_REGION_NAME": "sa-east-1",
    }


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    """Remove do ambiente todas as variáveis da aplicação.

    `LOG_DIR` aponta para uma pasta temporária: nenhum teste grava em `logs/` do repositório.
    """
    for name in ALL_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    return monkeypatch


@pytest.fixture
def load_settings(clean_env, valid_env):
    """Recarrega `config.settings` com o ambiente controlado pelo teste."""
    for name, value in valid_env.items():
        clean_env.setenv(name, value)

    def _load(**overrides):
        for name, value in overrides.items():
            clean_env.setenv(name, value)
        return importlib.reload(config.settings)

    yield _load

    clean_env.undo()
    importlib.reload(config.settings)
