from django.contrib import admin

from apps.audiences.models import TargetAudience
from apps.core.admin import ActiveToggleActionsMixin


@admin.register(TargetAudience)
class TargetAudienceAdmin(ActiveToggleActionsMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
