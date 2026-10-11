from rest_framework.test import APIClient


def test_health_returns_ok():
    response = APIClient().get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_rejects_other_methods():
    response = APIClient().post("/api/v1/health/")

    assert response.status_code == 405
