from types import SimpleNamespace

from config.unfold_settings import UNFOLD, _can_view


def test_menu_items_are_only_shown_with_the_view_permission():
    sections = UNFOLD["SIDEBAR"]["navigation"]
    item = sections[0]["items"][0]
    allowed = SimpleNamespace(
        user=SimpleNamespace(has_perm=lambda perm: perm == "activities.view_activity")
    )
    denied = SimpleNamespace(user=SimpleNamespace(has_perm=lambda perm: False))
    assert item["permission"](allowed) is True
    assert item["permission"](denied) is False


def test_can_view_checks_the_given_permission():
    request = SimpleNamespace(user=SimpleNamespace(has_perm=lambda perm: perm == "x.view_y"))
    assert _can_view("x.view_y")(request) is True
    assert _can_view("x.view_z")(request) is False
