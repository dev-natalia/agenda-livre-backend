from django.contrib import admin

from apps.audiences.admin import TargetAudienceAdmin
from apps.audiences.models import TargetAudience
from apps.core.admin import ActiveToggleActionsMixin
from apps.core.models import CatalogModel


def test_extends_catalog_model_with_portuguese_labels():
    assert issubclass(TargetAudience, CatalogModel)
    assert TargetAudience._meta.verbose_name == "Público-alvo"
    assert TargetAudience._meta.verbose_name_plural == "Públicos-alvo"
    assert TargetAudience._meta.ordering == ["name"]


def test_str_and_slug_generation():
    audience = TargetAudience(name=" Pessoas idosas ")

    audience.clean()

    assert str(audience) == "Pessoas idosas"
    assert audience.slug == "pessoas-idosas"


def test_is_registered_with_admin():
    assert isinstance(admin.site._registry[TargetAudience], TargetAudienceAdmin)


def test_admin_configuration():
    audience_admin = TargetAudienceAdmin(TargetAudience, admin.site)
    assert audience_admin.list_display == ("name", "slug", "is_active")
    assert audience_admin.list_filter == ("is_active",)
    assert audience_admin.search_fields == ("name",)
    assert audience_admin.readonly_fields == ("created_at", "updated_at")
    assert audience_admin.prepopulated_fields == {"slug": ("name",)}
    assert issubclass(TargetAudienceAdmin, ActiveToggleActionsMixin)
