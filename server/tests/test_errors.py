from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers


def test_wrong_method_keeps_the_allow_header(client):
    response = client.post("/api/auth/me")

    assert response.status_code == 405
    assert response.headers["allow"] == "GET"
    assert response.json() == {"error": {"code": "method_not_allowed", "message": "Method Not Allowed"}}


def test_unexpected_crash_returns_the_json_error_shape():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("database connection dropped")

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/crash")

    assert response.status_code == 500
    assert response.json() == {"error": {"code": "internal_error", "message": "Something went wrong on the server"}}
