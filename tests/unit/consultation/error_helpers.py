"""Apoio às verificações de privacidade: procura chaves internas em qualquer profundidade."""

FORBIDDEN_KEYS = {
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "status",
    "password",
    "secret",
    "is_staff",
    "is_superuser",
    "email",
    "username",
}


def find_forbidden_keys(value):
    """Devolve o conjunto de chaves proibidas presentes em dicts e listas aninhados."""
    found = set()
    if isinstance(value, dict):
        found |= FORBIDDEN_KEYS & set(value)
        for item in value.values():
            found |= find_forbidden_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            found |= find_forbidden_keys(item)
    return found
