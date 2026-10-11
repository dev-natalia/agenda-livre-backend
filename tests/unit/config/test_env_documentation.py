import re
from pathlib import Path

import pytest

from config.env import ALL_VARS, BASE_DIR

README = (BASE_DIR / "README.md").read_text(encoding="utf-8")
EXAMPLE = (BASE_DIR / ".env.example").read_text(encoding="utf-8")
GITIGNORE = (BASE_DIR / ".gitignore").read_text(encoding="utf-8").splitlines()


@pytest.mark.parametrize("name", ALL_VARS)
def test_variable_is_documented_in_readme_and_example(name):
    assert f"`{name}`" in README
    assert re.search(rf"^{name}=", EXAMPLE, re.MULTILINE)


def test_example_has_only_placeholder_values():
    assert "amazonaws.com" in EXAMPLE
    assert "seu-endpoint.rds.amazonaws.com" in EXAMPLE
    assert not re.search(r"[a-z0-9]{12,}\.[a-z0-9-]+\.rds\.amazonaws\.com", EXAMPLE)


def test_secrets_and_logs_are_not_versioned():
    assert ".env" in GITIGNORE
    assert "logs/" in GITIGNORE
    assert not Path(BASE_DIR / ".env.example").is_dir()
