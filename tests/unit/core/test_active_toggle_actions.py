from unittest.mock import MagicMock

from apps.core.admin import ActiveToggleActionsMixin


class _Admin(ActiveToggleActionsMixin):
    def __init__(self):
        self.message_user = MagicMock()


def test_deactivate_selected_updates_without_deleting():
    admin_obj, request, queryset = _Admin(), MagicMock(), MagicMock()
    queryset.update.return_value = 2

    admin_obj.deactivate_selected(request, queryset)

    queryset.update.assert_called_once_with(is_active=False)
    queryset.delete.assert_not_called()
    admin_obj.message_user.assert_called_once_with(request, "2 registro(s) desativado(s).")


def test_reactivate_selected_updates_without_deleting():
    admin_obj, request, queryset = _Admin(), MagicMock(), MagicMock()
    queryset.update.return_value = 3

    admin_obj.reactivate_selected(request, queryset)

    queryset.update.assert_called_once_with(is_active=True)
    queryset.delete.assert_not_called()
    admin_obj.message_user.assert_called_once_with(request, "3 registro(s) reativado(s).")


def test_actions_are_declared_with_portuguese_descriptions():
    assert ActiveToggleActionsMixin.actions == ["deactivate_selected", "reactivate_selected"]
    assert ActiveToggleActionsMixin.deactivate_selected.short_description == (
        "Desativar selecionados"
    )
    assert ActiveToggleActionsMixin.reactivate_selected.short_description == (
        "Reativar selecionados"
    )
