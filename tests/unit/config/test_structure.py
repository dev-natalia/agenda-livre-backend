import pytest
from django.conf import settings

DOMAIN_MODULES = [
    "apps.core",
    "apps.units",
    "apps.categories",
    "apps.activities",
    "apps.schedules",
    "apps.audiences",
]


@pytest.mark.parametrize("module", DOMAIN_MODULES)
def test_domain_modules_are_installed(module):
    assert module in settings.INSTALLED_APPS
