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


PENDING_MODULES = ["apps.schedules"]


def test_pending_domain_modules_define_no_business_models():
    from django.apps import apps

    for module in PENDING_MODULES:
        label = module.split(".")[-1]
        assert list(apps.get_app_config(label).get_models()) == []
