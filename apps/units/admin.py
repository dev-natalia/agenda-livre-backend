from django.contrib import admin

from apps.core.admin import ActiveOnlyForeignKeyMixin, ActiveToggleActionsMixin
from apps.units.models import Unit


@admin.register(Unit)
class UnitAdmin(ActiveToggleActionsMixin, ActiveOnlyForeignKeyMixin, admin.ModelAdmin):
    list_display = ("name", "neighborhood", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "neighborhood")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
