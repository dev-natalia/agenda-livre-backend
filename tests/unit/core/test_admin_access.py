from types import SimpleNamespace

import pytest
from django.contrib import admin
from django.test import RequestFactory
from django.urls import resolve

ANONYMOUS = SimpleNamespace(is_active=False, is_staff=False, is_authenticated=False)
INACTIVE = SimpleNamespace(is_active=False, is_staff=True, is_authenticated=True)
NOT_STAFF = SimpleNamespace(is_active=True, is_staff=False, is_authenticated=True)
STAFF = SimpleNamespace(is_active=True, is_staff=True, is_authenticated=True)


def _request(user):
    request = RequestFactory().get("/admin/")
    request.user = user
    return request


@pytest.mark.parametrize(
    ("user", "allowed"),
    [(ANONYMOUS, False), (INACTIVE, False), (NOT_STAFF, False), (STAFF, True)],
    ids=["anonimo", "inativo", "sem-is-staff", "ativo-e-staff"],
)
def test_admin_site_allows_only_active_staff(user, allowed):
    assert bool(admin.site.has_permission(_request(user))) is allowed


@pytest.mark.parametrize("path", ["/admin/", "/admin/login/"])
def test_admin_routes_are_wired(path):
    assert resolve(path).func is not None


def test_public_health_route_is_still_wired():
    assert resolve("/api/v1/health/").func is not None


def test_admin_branding_is_in_portuguese():
    assert "Administração" in admin.site.site_header
    assert admin.site.index_title
