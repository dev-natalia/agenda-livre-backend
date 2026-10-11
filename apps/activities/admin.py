from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html, format_html_join

from apps.activities.models import PUBLIC_STATUSES, Activity, ActivityTargetAudience
from apps.activities.services import StatusChangeError, change_status
from apps.core.admin import ActiveOnlyForeignKeyMixin
from apps.schedules.forms import ScheduleInlineForm
from apps.schedules.models import Schedule
from apps.schedules.services import sync_weekdays, upcoming_occurrences


class ActivityTargetAudienceFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        chosen = []
        for form in self.forms:
            if form.errors or not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE") or not form.cleaned_data.get("target_audience"):
                continue
            chosen.append(form.cleaned_data["target_audience"])
        if len(chosen) != len(set(chosen)):
            raise ValidationError(
                "A mesma opção de público-alvo não pode ser escolhida duas vezes."
            )
        if self.instance.status == Activity.Status.PUBLISHED and not chosen:
            raise ValidationError("Uma atividade publicada precisa de ao menos um público-alvo.")


class ActivityTargetAudienceInline(admin.TabularInline):
    model = ActivityTargetAudience
    formset = ActivityTargetAudienceFormSet
    extra = 1
    verbose_name = "Público-alvo"
    verbose_name_plural = "Públicos-alvo"
    _linked_ids = ()

    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None and obj.pk is not None:
            links = obj.audience_links.values_list("target_audience_id", flat=True)
            self._linked_ids = list(links)
        else:
            self._linked_ids = []
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "target_audience":
            queryset = kwargs.get("queryset")
            if queryset is None:
                queryset = db_field.remote_field.model._default_manager.all()
            kwargs["queryset"] = queryset.filter(Q(is_active=True) | Q(pk__in=self._linked_ids))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ScheduleInline(admin.StackedInline):
    model = Schedule
    form = ScheduleInlineForm
    extra = 1
    verbose_name = "Programação"
    verbose_name_plural = "Programações"


@admin.register(Activity)
class ActivityAdmin(ActiveOnlyForeignKeyMixin, admin.ModelAdmin):
    list_display = ("title", "unit", "category", "status", "updated_at")
    list_filter = ("status", "unit", "category")
    search_fields = ("title", "summary")
    list_select_related = ("unit", "category")
    readonly_fields = (
        "status",
        "slug",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
        "upcoming_occurrences_display",
    )
    fields = (
        "title",
        "summary",
        "description",
        "unit",
        "category",
        "target_audience_notes",
        "external_registration_url",
        "status",
        "slug",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
        "upcoming_occurrences_display",
    )
    inlines = [ActivityTargetAudienceInline, ScheduleInline]
    actions = ["publish_selected", "cancel_selected", "finish_selected"]

    @admin.display(description="Próximas ocorrências")
    def upcoming_occurrences_display(self, obj):
        if obj is None or obj.pk is None:
            return "Salve a atividade para ver as próximas ocorrências."
        if obj.status not in PUBLIC_STATUSES:
            return "Sem ocorrências: a atividade não está publicada."
        occurrences = upcoming_occurrences(obj)
        if not occurrences:
            return "Sem próximas ocorrências."
        return format_html(
            "<ul>{}</ul>",
            format_html_join(
                "",
                "<li>{}, {}–{}</li>",
                (
                    (
                        item.date.strftime("%d/%m/%Y"),
                        item.start_time.strftime("%H:%M"),
                        item.end_time.strftime("%H:%M"),
                    )
                    for item in occurrences
                ),
            ),
        )

    def save_formset(self, request, form, formset, change):
        if formset.model is not Schedule:
            return super().save_formset(request, form, formset, change)
        saved = formset.save(commit=False)
        for removed in formset.deleted_objects:
            removed.delete()
        for schedule in saved:
            if schedule._state.adding:
                schedule.created_by = request.user
            schedule.updated_by = request.user
            schedule.save()
        for schedule_form in formset.forms:
            if schedule_form.instance in saved:
                sync_weekdays(schedule_form.instance, schedule_form.cleaned_data.get("weekdays"))
        formset.save_m2m()

    def get_form(self, request, obj=None, **kwargs):
        request._editing_obj = obj
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        allowed = super().has_delete_permission(request, obj)
        if obj is None:
            return allowed
        return allowed and obj.status == Activity.Status.DRAFT

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def _apply_status(self, request, queryset, new_status, done_label):
        changed = 0
        for activity in queryset:
            try:
                changed += change_status(activity, new_status, request.user)
            except StatusChangeError as error:
                self.message_user(request, f"{activity.title}: {error}", messages.ERROR)
        if changed:
            self.message_user(request, f"{changed} atividade(s) {done_label}.", messages.SUCCESS)

    @admin.action(description="Publicar selecionadas", permissions=["change"])
    def publish_selected(self, request, queryset):
        self._apply_status(request, queryset, Activity.Status.PUBLISHED, "publicada(s)")

    @admin.action(description="Cancelar selecionadas", permissions=["change"])
    def cancel_selected(self, request, queryset):
        self._apply_status(request, queryset, Activity.Status.CANCELLED, "cancelada(s)")

    @admin.action(description="Encerrar selecionadas", permissions=["change"])
    def finish_selected(self, request, queryset):
        self._apply_status(request, queryset, Activity.Status.FINISHED, "encerrada(s)")
