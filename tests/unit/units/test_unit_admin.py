from django.contrib import admin

from apps.core.admin import ActiveOnlyForeignKeyMixin, ActiveToggleActionsMixin
from apps.units.admin import UnitAdmin
from apps.units.models import Unit


def test_unit_is_registered_with_unit_admin():
    assert isinstance(admin.site._registry[Unit], UnitAdmin)


def test_list_configuration():
    unit_admin = UnitAdmin(Unit, admin.site)
    assert unit_admin.list_display == ("name", "neighborhood", "slug", "is_active")
    assert unit_admin.list_filter == ("is_active",)
    assert unit_admin.search_fields == ("name", "neighborhood")


def test_form_configuration():
    unit_admin = UnitAdmin(Unit, admin.site)
    assert unit_admin.readonly_fields == ("created_at", "updated_at")
    assert unit_admin.prepopulated_fields == {"slug": ("name",)}


def test_inherits_active_mixins():
    assert issubclass(UnitAdmin, ActiveToggleActionsMixin)
    assert issubclass(UnitAdmin, ActiveOnlyForeignKeyMixin)
