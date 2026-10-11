from types import SimpleNamespace

from apps.core.exceptions import public_exception_handler

SECRET = "sentinela-super-secreta-123"


def test_secrets_never_reach_the_response_body_or_the_request_log_line(caplog):
    request = SimpleNamespace(
        method="GET",
        path="/api/v1/activities/",
        headers={"Authorization": SECRET},
        META={"HTTP_COOKIE": SECRET},
        body=SECRET.encode(),
        GET={"q": SECRET},
    )
    with caplog.at_level("ERROR", logger="apps.core.exceptions"):
        error = RuntimeError(f"falha com {SECRET}")
        response = public_exception_handler(error, {"request": request})
    assert SECRET not in str(response.data)
    assert SECRET not in caplog.records[0].getMessage()
