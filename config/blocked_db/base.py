"""Backend de banco de dados que recusa qualquer uso. Exclusivo para os testes.

Baseia-se no backend `dummy` do Django, trocando a mensagem de erro por uma que deixa explícito
que o acesso ao banco é proibido nos testes unitários.
"""

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.dummy import base as dummy


def complain(*args, **kwargs):
    raise ImproperlyConfigured(
        "Acesso a banco de dados proibido nos testes: os testes devem ser unitários e usar mocks."
    )


class DatabaseOperations(dummy.DatabaseOperations):
    quote_name = complain


class DatabaseWrapper(dummy.DatabaseWrapper):
    _cursor = complain
    ensure_connection = complain
    _commit = complain
    _savepoint_commit = complain
    _set_autocommit = complain
    ops_class = DatabaseOperations
