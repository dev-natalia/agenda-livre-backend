"""Garante que os testes não conseguem acessar nenhum banco de dados."""

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import connection

FORBIDDEN = "Acesso a banco de dados proibido nos testes"


def test_tests_use_the_blocked_database_engine():
    assert settings.DATABASES["default"]["ENGINE"] == "config.blocked_db"


def test_opening_a_connection_fails_with_explicit_message():
    with pytest.raises(ImproperlyConfigured, match=FORBIDDEN):
        connection.ensure_connection()


def test_cursor_fails_with_explicit_message():
    with pytest.raises(ImproperlyConfigured, match=FORBIDDEN):
        connection.cursor()


def test_orm_query_fails_with_explicit_message():
    with pytest.raises(ImproperlyConfigured, match=FORBIDDEN):
        User.objects.count()


def test_quoting_names_fails_with_explicit_message():
    with pytest.raises(ImproperlyConfigured, match=FORBIDDEN):
        connection.ops.quote_name("tabela")

