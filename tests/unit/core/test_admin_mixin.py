from types import SimpleNamespace
from unittest.mock import MagicMock

from django.contrib import admin
from django.db.models import Q

from apps.core.admin import ActiveOnlyForeignKeyMixin


class _Base:
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return kwargs


class _ModelAdmin(ActiveOnlyForeignKeyMixin, _Base):
    pass


def _db_field(field_names):
    model = MagicMock()
    model._meta.get_fields.return_value = [SimpleNamespace(name=n) for n in field_names]
    return SimpleNamespace(name="unit", remote_field=SimpleNamespace(model=model)), model


def test_filters_inactive_records_from_default_queryset():
    db_field, model = _db_field(["id", "name", "is_active"])

    result = _ModelAdmin().formfield_for_foreignkey(db_field, None)

    default = model._default_manager.all.return_value
    default.filter.assert_called_once_with(is_active=True)
    assert result["queryset"] is default.filter.return_value


def test_filters_inactive_records_from_given_queryset():
    db_field, model = _db_field(["is_active"])
    given = MagicMock()

    result = _ModelAdmin().formfield_for_foreignkey(db_field, None, queryset=given)

    given.filter.assert_called_once_with(is_active=True)
    assert result["queryset"] is given.filter.return_value
    model._default_manager.all.assert_not_called()


def test_leaves_queryset_alone_without_is_active_field():
    db_field, model = _db_field(["id", "name"])

    result = _ModelAdmin().formfield_for_foreignkey(db_field, None)

    assert "queryset" not in result
    model._default_manager.all.assert_not_called()


def test_admin_module_keeps_default_site_registered():
    assert admin.site.site_header


def test_keeps_current_value_of_record_in_edition():
    db_field, model = _db_field(["is_active"])
    db_field.name = "unit"
    request = SimpleNamespace(_editing_obj=SimpleNamespace(unit_id="abc"))

    result = _ModelAdmin().formfield_for_foreignkey(db_field, request)

    default = model._default_manager.all.return_value
    default.filter.assert_called_once()
    assert default.filter.call_args.args[0] == (Q(is_active=True) | Q(pk="abc"))
    assert result["queryset"] is default.filter.return_value


def test_filters_only_active_when_editing_object_has_no_current_value():
    db_field, model = _db_field(["is_active"])
    db_field.name = "unit"
    request = SimpleNamespace(_editing_obj=SimpleNamespace(unit_id=None))

    _ModelAdmin().formfield_for_foreignkey(db_field, request)

    model._default_manager.all.return_value.filter.assert_called_once_with(is_active=True)
