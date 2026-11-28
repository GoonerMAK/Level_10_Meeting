import asyncio
import json
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers
from app.core.logs import JsonFormatter, RequestLog, logger


@pytest.fixture
def log_lines():
    lines = []

    class Collect(logging.Handler):
        def emit(self, record):
            lines.append(json.loads(JsonFormatter().format(record)))

    handler = Collect()
    logger.addHandler(handler)
    yield lines
    logger.removeHandler(handler)


def test_a_refused_request_is_logged_with_its_request_id(sign_in, log_lines):
    response = sign_in("u2").get("/api/teams/team_ops")

    [line] = [line for line in log_lines if line["message"] == "Request refused"]
    assert line["request_id"] == response.headers["x-request-id"]
    assert {key: line[key] for key in ("level", "method", "path", "status", "user_id", "error_code")} == {
        "level": "info",
        "method": "GET",
        "path": "/api/teams/team_ops",
        "status": 404,
        "user_id": "u2",
        "error_code": "not_found",
    }


def test_a_successful_request_writes_no_log_but_still_gets_an_id(sign_in, log_lines):
    response = sign_in("u2").get("/api/teams/team_lead")

    assert response.status_code == 200
    assert len(response.headers["x-request-id"]) == 32
    assert [line for line in log_lines if line.get("path") == "/api/teams/team_lead"] == []


def test_a_request_id_sent_by_the_browser_is_kept(sign_in):
    response = sign_in("u2").get("/api/teams/team_lead", headers={"x-request-id": "bug-report-1234"})

    assert response.headers["x-request-id"] == "bug-report-1234"


def logged_app(slow_after_ms):
    app = FastAPI()
    register_error_handlers(app)
    app.add_middleware(RequestLog, slow_after_ms=slow_after_ms)

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("database connection dropped")

    @app.get("/slow")
    async def slow() -> dict[str, bool]:
        await asyncio.sleep(0.02)
        return {"ok": True}

    return TestClient(app, raise_server_exceptions=False)


def test_a_crash_is_logged_with_its_traceback_and_the_id_is_returned(log_lines):
    with logged_app(slow_after_ms=500) as client:
        response = client.get("/crash")

    [line] = log_lines
    assert response.status_code == 500
    assert response.headers["x-request-id"] == line["request_id"]
    assert (line["level"], line["message"], line["status"]) == ("error", "Request crashed", 500)
    assert "RuntimeError: database connection dropped" in line["error"]


def test_a_slow_request_is_logged_as_a_warning(log_lines):
    with logged_app(slow_after_ms=10) as client:
        client.get("/slow")

    [line] = log_lines
    assert (line["level"], line["message"], line["status"]) == ("warning", "Slow request", 200)
    assert line["duration_ms"] >= 10
