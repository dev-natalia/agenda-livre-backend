import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.consultation.pagination import PublicPagination
from apps.core.exceptions import public_exception_handler


def _page(items, query=""):
    request = Request(APIRequestFactory().get("/api/v1/activities/" + query))
    paginator = PublicPagination()
    page = paginator.paginate_queryset(items, request, view=APIView())
    return paginator.get_paginated_response(page).data


def test_default_page_size_is_12():
    assert len(_page(list(range(30)))["results"]) == 12


@pytest.mark.parametrize("value", ["0", "-3", "abc"])
def test_invalid_page_size_uses_default(value):
    assert len(_page(list(range(30)), f"?page_size={value}")["results"]) == 12


def test_page_size_is_capped_at_50():
    assert len(_page(list(range(80)), "?page_size=500")["results"]) == 50


def test_second_page_links_and_count():
    data = _page(list(range(30)), "?page=2")
    assert data["count"] == 30
    assert len(data["results"]) == 12
    assert data["previous"] and data["next"]


@pytest.mark.parametrize("query", ["?page=99", "?page=abc", "?page=0"])
def test_invalid_page_is_a_validation_error_on_page(query):
    with pytest.raises(ValidationError) as error:
        _page(list(range(30)), query)
    assert error.value.detail == {"page": ["Informe uma página válida."]}
    response = public_exception_handler(error.value, {"request": None})
    assert response.status_code == 400
    assert response.data["errors"] == {"page": ["Informe uma página válida."]}


def test_empty_list():
    data = _page([])
    assert data["count"] == 0 and data["results"] == []
