from django.contrib import admin

from apps.categories.admin import CategoryAdmin
from apps.categories.models import Category
from apps.core.admin import ActiveOnlyForeignKeyMixin, ActiveToggleActionsMixin


def test_category_is_registered_with_category_admin():
    assert isinstance(admin.site._registry[Category], CategoryAdmin)


def test_list_configuration():
    category_admin = CategoryAdmin(Category, admin.site)
    assert category_admin.list_display == ("name", "slug", "is_active")
    assert category_admin.list_filter == ("is_active",)
    assert category_admin.search_fields == ("name",)


def test_form_configuration():
    category_admin = CategoryAdmin(Category, admin.site)
    assert category_admin.readonly_fields == ("created_at", "updated_at")
    assert category_admin.prepopulated_fields == {"slug": ("name",)}


def test_inherits_active_mixins():
    assert issubclass(CategoryAdmin, ActiveToggleActionsMixin)
    assert issubclass(CategoryAdmin, ActiveOnlyForeignKeyMixin)
