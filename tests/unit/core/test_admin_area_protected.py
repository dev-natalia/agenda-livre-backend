from types import SimpleNamespace

import pytest
from django.contrib import admin
from django.test import RequestFactory


def _request(**user):
    request = RequestFactory().get("/admin/")
    request.user = SimpleNamespace(**user)
    return request


@pytest.mark.parametrize(
    "user",
    [
        {"is_active": False, "is_staff": True},
        {"is_active": True, "is_staff": False},
        {"is_active": False, "is_staff": False},
    ],
)
def test_management_area_refuses_anonymous_inactive_and_non_staff(user):
    assert admin.site.has_permission(_request(**user)) is False


def test_management_area_accepts_active_staff():
    assert admin.site.has_permission(_request(is_active=True, is_staff=True)) is True


def test_management_index_redirects_unauthenticated_visitors_to_login():
    request = _request(is_active=False, is_staff=False)
    response = admin.site.admin_view(lambda req: "conteudo")(request)
    assert response.status_code == 302
    assert "login" in response.url
