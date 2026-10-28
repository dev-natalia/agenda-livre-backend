from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.categories.models import Category
from apps.core.admin import ActiveOnlyForeignKeyMixin, ActiveToggleActionsMixin


@admin.register(Category)
class CategoryAdmin(ActiveToggleActionsMixin, ActiveOnlyForeignKeyMixin, ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
