from datetime import date, time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.test import RequestFactory

from apps.activities import admin as activity_admin_module
from apps.activities.admin import (
    ActivityAdmin,
    ActivityTargetAudienceFormSet,
    ActivityTargetAudienceInline,
    ScheduleInline,
)
from apps.activities.models import Activity, ActivityTargetAudience
from apps.activities.services import StatusChangeError
from apps.core.admin import ActiveOnlyForeignKeyMixin
from apps.schedules.forms import ScheduleInlineForm
from apps.schedules.models import Schedule

Status = Activity.Status


@pytest.fixture
def model_admin():
    return ActivityAdmin(Activity, admin.site)


def _request():
    request = RequestFactory().get("/")
    request.user = SimpleNamespace(pk=1)
    return request


def test_is_registered(model_admin):
    assert isinstance(admin.site._registry[Activity], ActivityAdmin)
    assert issubclass(ActivityAdmin, ActiveOnlyForeignKeyMixin)


def test_list_configuration(model_admin):
    assert model_admin.list_display == ("title", "unit", "category", "status", "updated_at")
    assert model_admin.list_filter == ("status", "unit", "category")
    assert model_admin.search_fields == ("title", "summary")
    assert model_admin.list_select_related == ("unit", "category")


def test_form_configuration(model_admin):
    assert model_admin.readonly_fields == (
        "image_preview",
        "status",
        "slug",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
        "upcoming_occurrences_display",
    )
    assert model_admin.inlines == [ActivityTargetAudienceInline, ScheduleInline]


def test_actions_order_and_labels(model_admin):
    assert model_admin.actions == ["publish_selected", "cancel_selected", "finish_selected"]
    labels = [
        model_admin.publish_selected.short_description,
        model_admin.cancel_selected.short_description,
        model_admin.finish_selected.short_description,
    ]
    assert labels == ["Publicar selecionadas", "Cancelar selecionadas", "Encerrar selecionadas"]
    for action in (model_admin.publish_selected, model_admin.cancel_selected):
        assert action.allowed_permissions == ["change"]


def test_get_actions_removes_bulk_delete(model_admin):
    request = _request()
    with patch.object(
        admin.ModelAdmin, "get_actions", return_value={"delete_selected": 1, "x": 2}
    ):
        assert model_admin.get_actions(request) == {"x": 2}


def test_get_form_stores_editing_object(model_admin):
    request, obj = _request(), object()
    with patch.object(admin.ModelAdmin, "get_form", return_value="form"):
        assert model_admin.get_form(request, obj) == "form"
    assert request._editing_obj is obj

    with patch.object(admin.ModelAdmin, "get_form", return_value="form"):
        model_admin.get_form(request)
    assert request._editing_obj is None


def test_save_model_on_create_sets_both_authors(model_admin):
    request, obj = _request(), SimpleNamespace()
    with patch.object(admin.ModelAdmin, "save_model") as parent:
        model_admin.save_model(request, obj, None, change=False)
    assert obj.created_by is request.user
    assert obj.updated_by is request.user
    parent.assert_called_once()


def test_save_model_on_edit_keeps_creator(model_admin):
    request = _request()
    creator = object()
    obj = SimpleNamespace(created_by=creator)
    with patch.object(admin.ModelAdmin, "save_model"):
        model_admin.save_model(request, obj, None, change=True)
    assert obj.created_by is creator
    assert obj.updated_by is request.user


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (Status.DRAFT, True),
        (Status.PUBLISHED, False),
        (Status.FINISHED, False),
        (Status.CANCELLED, False),
    ],
)
def test_only_drafts_can_be_deleted(model_admin, status, expected):
    obj = SimpleNamespace(status=status)
    with patch.object(admin.ModelAdmin, "has_delete_permission", return_value=True):
        assert model_admin.has_delete_permission(_request(), obj) is expected


def test_delete_permission_without_object_follows_parent(model_admin):
    with patch.object(admin.ModelAdmin, "has_delete_permission", return_value=True):
        assert model_admin.has_delete_permission(_request()) is True


def test_delete_permission_denied_by_parent_stays_denied(model_admin):
    obj = SimpleNamespace(status=Status.DRAFT)
    with patch.object(admin.ModelAdmin, "has_delete_permission", return_value=False):
        assert model_admin.has_delete_permission(_request(), obj) is False


# --- ações de situação ---


@pytest.mark.parametrize(
    ("action", "status", "label"),
    [
        ("publish_selected", Status.PUBLISHED, "publicada(s)"),
        ("cancel_selected", Status.CANCELLED, "cancelada(s)"),
        ("finish_selected", Status.FINISHED, "encerrada(s)"),
    ],
)
def test_actions_call_change_status_and_report_count(model_admin, action, status, label):
    request = _request()
    activities = [SimpleNamespace(title="A"), SimpleNamespace(title="B")]
    model_admin.message_user = MagicMock()
    with patch.object(activity_admin_module, "change_status", return_value=True) as change:
        getattr(model_admin, action)(request, activities)

    assert [call.args for call in change.call_args_list] == [
        (activities[0], status, request.user),
        (activities[1], status, request.user),
    ]
    model_admin.message_user.assert_called_once_with(
        request, f"2 atividade(s) {label}.", messages.SUCCESS
    )


def test_action_reports_refused_activities_with_reason(model_admin):
    request = _request()
    activities = [SimpleNamespace(title="A"), SimpleNamespace(title="B")]
    model_admin.message_user = MagicMock()
    with patch.object(
        activity_admin_module,
        "change_status",
        side_effect=[StatusChangeError("Falta ao menos um público-alvo."), True],
    ):
        model_admin.publish_selected(request, activities)

    model_admin.message_user.assert_any_call(
        request, "A: Falta ao menos um público-alvo.", messages.ERROR
    )
    model_admin.message_user.assert_any_call(
        request, "1 atividade(s) publicada(s).", messages.SUCCESS
    )


def test_action_ignores_activities_already_in_status(model_admin):
    model_admin.message_user = MagicMock()
    with patch.object(activity_admin_module, "change_status", return_value=False):
        model_admin.cancel_selected(_request(), [SimpleNamespace(title="A")])

    model_admin.message_user.assert_not_called()


# --- inline de públicos-alvo ---


def _form(audience=None, delete=False, errors=None, has_data=True):
    form = SimpleNamespace(errors=errors or {})
    if has_data:
        form.cleaned_data = {"target_audience": audience, "DELETE": delete}
    return form


def _formset(forms, status):
    formset = ActivityTargetAudienceFormSet.__new__(ActivityTargetAudienceFormSet)
    formset.forms = forms
    formset.instance = SimpleNamespace(status=status)
    return formset


def _run_clean(formset):
    with patch("django.forms.models.BaseInlineFormSet.clean"):
        formset.clean()


def test_formset_rejects_duplicate_audience():
    audience = object()
    formset = _formset([_form(audience), _form(audience)], Status.DRAFT)

    with pytest.raises(ValidationError, match="duas vezes"):
        _run_clean(formset)


def test_formset_ignores_deleted_empty_and_invalid_forms():
    audience = object()
    formset = _formset(
        [
            _form(audience),
            _form(audience, delete=True),
            _form(None),
            _form(audience, errors={"x": "erro"}),
            _form(has_data=False),
        ],
        Status.DRAFT,
    )

    _run_clean(formset)


def test_formset_requires_audience_for_published_activity():
    formset = _formset([_form(None), _form(object(), delete=True)], Status.PUBLISHED)

    with pytest.raises(ValidationError, match="publicada"):
        _run_clean(formset)


def test_formset_accepts_published_activity_with_audience():
    _run_clean(_formset([_form(object())], Status.PUBLISHED))


def test_formset_accepts_draft_without_audience():
    _run_clean(_formset([], Status.DRAFT))


def test_inline_configuration():
    assert ActivityTargetAudienceInline.model is ActivityTargetAudience
    assert ActivityTargetAudienceInline.formset is ActivityTargetAudienceFormSet
    assert ActivityTargetAudienceInline.verbose_name_plural == "Públicos-alvo"


def test_inline_remembers_linked_ids_of_existing_activity():
    inline = ActivityTargetAudienceInline(Activity, admin.site)
    obj = MagicMock()
    obj.audience_links.values_list.return_value = ["a", "b"]
    with patch.object(admin.TabularInline, "get_formset", return_value="formset"):
        assert inline.get_formset(_request(), obj) == "formset"

    assert inline._linked_ids == ["a", "b"]


def test_inline_has_no_linked_ids_for_new_activity():
    inline = ActivityTargetAudienceInline(Activity, admin.site)
    with patch.object(admin.TabularInline, "get_formset", return_value="formset"):
        inline.get_formset(_request(), None)

    assert inline._linked_ids == []


def test_inline_offers_active_audiences_and_the_linked_ones():
    inline = ActivityTargetAudienceInline(Activity, admin.site)
    inline._linked_ids = ["a"]
    model = MagicMock()
    db_field = SimpleNamespace(name="target_audience", remote_field=SimpleNamespace(model=model))
    with patch.object(
        admin.TabularInline, "formfield_for_foreignkey", side_effect=lambda f, r, **kw: kw
    ):
        result = inline.formfield_for_foreignkey(db_field, _request())

    model._default_manager.all.return_value.filter.assert_called_once()
    assert result["queryset"] is model._default_manager.all.return_value.filter.return_value


def test_inline_leaves_other_foreign_keys_alone():
    inline = ActivityTargetAudienceInline(Activity, admin.site)
    db_field = SimpleNamespace(name="activity")
    with patch.object(
        admin.TabularInline, "formfield_for_foreignkey", side_effect=lambda f, r, **kw: kw
    ):
        assert inline.formfield_for_foreignkey(db_field, _request()) == {}


def test_inline_uses_given_queryset():
    inline = ActivityTargetAudienceInline(Activity, admin.site)
    given = MagicMock()
    db_field = SimpleNamespace(name="target_audience")
    with patch.object(
        admin.TabularInline, "formfield_for_foreignkey", side_effect=lambda f, r, **kw: kw
    ):
        result = inline.formfield_for_foreignkey(db_field, _request(), queryset=given)

    assert result["queryset"] is given.filter.return_value


def test_schedule_inline_configuration():
    inline = ScheduleInline(Activity, admin.site)
    assert inline.model is Schedule
    assert inline.form is ScheduleInlineForm
    assert inline.extra == 1
    assert inline.verbose_name_plural == "Programações"


def test_occurrences_display_without_object(model_admin):
    assert "Salve a atividade" in model_admin.upcoming_occurrences_display(None)


@pytest.mark.parametrize("status", [Status.DRAFT, Status.CANCELLED, Status.FINISHED])
def test_occurrences_display_not_published(model_admin, status):
    activity = Activity(status=status)
    with patch.object(activity_admin_module, "upcoming_occurrences") as service:
        text = model_admin.upcoming_occurrences_display(activity)
    service.assert_not_called()
    assert text == "Sem ocorrências: a atividade não está publicada."


def test_occurrences_display_empty(model_admin):
    activity = Activity(status=Status.PUBLISHED)
    with patch.object(activity_admin_module, "upcoming_occurrences", return_value=[]):
        assert model_admin.upcoming_occurrences_display(activity) == "Sem próximas ocorrências."


def test_occurrences_display_lists_occurrences(model_admin):
    activity = Activity(status=Status.PUBLISHED)
    found = [
        SimpleNamespace(date=date(2026, 11, 10), start_time=time(14), end_time=time(15, 30)),
        SimpleNamespace(date=date(2026, 11, 12), start_time=time(9), end_time=time(10)),
    ]
    with patch.object(activity_admin_module, "upcoming_occurrences", return_value=found):
        text = str(model_admin.upcoming_occurrences_display(activity))
    assert "<li>10/11/2026, 14:00–15:30</li>" in text
    assert "<li>12/11/2026, 09:00–10:00</li>" in text


def _schedule_formset(saved, deleted=(), forms=()):
    formset = MagicMock()
    formset.model = Schedule
    formset.save.return_value = saved
    formset.deleted_objects = list(deleted)
    formset.forms = list(forms)
    return formset


def _saved(adding):
    return SimpleNamespace(_state=SimpleNamespace(adding=adding), save=MagicMock())


def test_save_formset_delegates_other_models(model_admin):
    formset = MagicMock()
    formset.model = ActivityTargetAudience
    with patch.object(admin.ModelAdmin, "save_formset") as parent:
        model_admin.save_formset(_request(), None, formset, True)
    parent.assert_called_once()


def test_save_formset_sets_audit_and_syncs_weekdays(model_admin):
    request = _request()
    new, old = _saved(True), _saved(False)
    old.created_by = "original"
    removed = MagicMock()
    forms = [
        SimpleNamespace(instance=new, cleaned_data={"weekdays": [2, 4]}),
        SimpleNamespace(instance=old, cleaned_data={"weekdays": []}),
        SimpleNamespace(instance=_saved(False), cleaned_data={"weekdays": [1]}),
    ]
    formset = _schedule_formset([new, old], deleted=[removed], forms=forms)
    with patch.object(activity_admin_module, "sync_weekdays") as sync:
        model_admin.save_formset(request, None, formset, True)
    assert new.created_by is request.user
    assert old.created_by == "original"
    assert new.updated_by is request.user and old.updated_by is request.user
    new.save.assert_called_once()
    old.save.assert_called_once()
    removed.delete.assert_called_once()
    assert [call.args for call in sync.call_args_list] == [(new, [2, 4]), (old, [])]
    formset.save_m2m.assert_called_once()
