import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib import admin
from django.db.models import Q
from django.test import RequestFactory
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from apps.activities import admin as activity_admin
from apps.activities.admin import ActivityAdmin, AudienceListFilter
from apps.activities.models import Activity


def _request():
    request = RequestFactory().get("/admin/activities/activity/")
    request.user = SimpleNamespace(pk=1)
    return request


def _filter(params=None, audiences=()):
    """Cria o filtro com a consulta de públicos-alvo simulada."""
    with patch.object(activity_admin, "TargetAudience") as model:
        chain = model.objects.filter.return_value.distinct.return_value.order_by
        chain.return_value = list(audiences)
        instance = AudienceListFilter(
            _request(), params or {}, Activity, ActivityAdmin(Activity, admin.site)
        )
    instance.model_mock = model
    return instance


def _audience(name):
    return SimpleNamespace(pk=uuid.uuid4(), name=name)


def test_filter_identity():
    assert AudienceListFilter.title == "Público-alvo"
    assert AudienceListFilter.parameter_name == "audience"


def test_lookups_list_audiences_by_name_with_their_ids():
    adults, children = _audience("Adultos"), _audience("Crianças")

    instance = _filter(audiences=[adults, children])

    assert instance.lookup_choices == [(str(adults.pk), "Adultos"), (str(children.pk), "Crianças")]


def test_lookups_ask_for_active_audiences_and_inactive_ones_with_activities():
    instance = _filter()
    model = instance.model_mock

    (condition,), _ = model.objects.filter.call_args
    assert condition == Q(is_active=True) | Q(activity_links__isnull=False)
    model.objects.filter.return_value.distinct.assert_called_once_with()
    model.objects.filter.return_value.distinct.return_value.order_by.assert_called_once_with("name")


def test_without_a_value_the_queryset_is_returned_untouched():
    instance = _filter()
    queryset = MagicMock()

    assert instance.queryset(_request(), queryset) is queryset
    queryset.filter.assert_not_called()


def test_with_a_value_it_filters_by_the_linked_audience():
    chosen = uuid.uuid4()
    instance = _filter({"audience": [str(chosen)]}, audiences=[_audience("Adultos")])
    queryset = MagicMock()

    result = instance.queryset(_request(), queryset)

    queryset.filter.assert_called_once_with(audience_links__target_audience_id=str(chosen))
    assert result is queryset.filter.return_value


def test_filter_is_in_the_activity_list_filters():
    assert ActivityAdmin(Activity, admin.site).list_filter == (
        "status",
        "unit",
        "category",
        AudienceListFilter,
    )


def test_search_actions_and_delete_rules_are_unchanged():
    model_admin = ActivityAdmin(Activity, admin.site)

    assert model_admin.search_fields == ("title", "summary")
    assert model_admin.actions == ["publish_selected", "cancel_selected", "finish_selected"]
    request = _request()
    with patch.object(UnfoldModelAdmin, "has_delete_permission", return_value=True):
        draft = SimpleNamespace(status=Activity.Status.DRAFT)
        published = SimpleNamespace(status=Activity.Status.PUBLISHED)
        assert model_admin.has_delete_permission(request, draft) is True
        assert model_admin.has_delete_permission(request, published) is False
