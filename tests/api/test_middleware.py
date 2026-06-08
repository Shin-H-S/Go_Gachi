import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.middlewares import AccessLogMiddleware, RequestIDMiddleware
from backend.app.core.request_context import request_id_var


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestIDMiddleware)

    @app.get("/ok")
    async def ok() -> dict[str, str]:
        return {"request_id": request_id_var.get()}

    @app.get("/boom")
    async def boom() -> dict[str, str]:
        raise RuntimeError("boom")

    return app


def test_request_id_header_is_generated_and_available_in_context() -> None:
    client = TestClient(create_test_app())

    response = client.get("/ok")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_request_id_header_preserves_client_value() -> None:
    client = TestClient(create_test_app())

    response = client.get("/ok", headers={"X-Request-ID": "client-req-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "client-req-123"
    assert response.json()["request_id"] == "client-req-123"


def test_access_log_records_completed_request(caplog) -> None:
    client = TestClient(create_test_app())

    with caplog.at_level(logging.INFO, logger="backend.access"):
        response = client.get("/ok", headers={"X-Request-ID": "log-req-123"})

    assert response.status_code == 200
    assert "GET /ok status=200" in caplog.text
    assert "took=" in caplog.text


def test_unhandled_error_response_keeps_request_id_header(caplog) -> None:
    client = TestClient(create_test_app(), raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger="backend.access"):
        response = client.get("/boom", headers={"X-Request-ID": "boom-req-123"})

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "boom-req-123"
    assert response.json() == {"detail": "Internal Server Error"}
    assert "GET /boom failed" in caplog.text
