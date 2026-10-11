from django.contrib import admin

from apps.schedules.forms import ScheduleAdminForm
from apps.schedules.models import Schedule
from apps.schedules.services import format_weekdays, sync_weekdays


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    form = ScheduleAdminForm
    list_display = (
        "activity",
        "schedule_type",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "weekday_names",
        "updated_at",
    )
    list_filter = ("schedule_type", "start_date", "end_date")
    search_fields = ("activity__title",)
    list_select_related = ("activity",)
    autocomplete_fields = ("activity",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    fields = (
        "activity",
        "schedule_type",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "weekdays",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("weekdays")

    @admin.display(description="Dias da semana")
    def weekday_names(self, obj):
        return format_weekdays(obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        sync_weekdays(form.instance, form.cleaned_data.get("weekdays"))
