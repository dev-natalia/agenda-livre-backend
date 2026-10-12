from types import SimpleNamespace

from django.contrib import admin
from django.test import RequestFactory

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
    assert audience_admin.list_display == ("name", "slug", "is_active", "includes_everyone")
    assert audience_admin.list_filter == ("is_active", "includes_everyone")
    assert audience_admin.search_fields == ("name",)
    assert audience_admin.readonly_fields == ("created_at", "updated_at")
    assert audience_admin.prepopulated_fields == {"slug": ("name",)}
    assert issubclass(TargetAudienceAdmin, ActiveToggleActionsMixin)


def test_admin_form_offers_the_everyone_mark():
    audience_admin = TargetAudienceAdmin(TargetAudience, admin.site)
    request = RequestFactory().get("/")
    request.user = SimpleNamespace(pk=1, is_active=True, is_staff=True, is_superuser=True)

    form = audience_admin.get_form(request)

    assert "includes_everyone" in form.base_fields
    assert form.base_fields["includes_everyone"].initial is False
    assert "includes_everyone" not in audience_admin.readonly_fields
