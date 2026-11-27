import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers

BAD_INPUTS = [
    pytest.param("post", "/api/teams/team_lead/issues", {"title": "Hiring plan", "priority": 6}, "priority",
                 "Priority must be 1 to 5", id="priority_6"),
    pytest.param("post", "/api/teams/team_lead/issues", {"title": "   "}, "title",
                 "Title is required, up to 200 characters", id="blank_title"),
    pytest.param("post", "/api/issues/i1/solve", {"resolution_note": ""}, "resolution_note",
                 "A note is required to solve an Issue, up to 2,000 characters", id="solve_without_note"),
    pytest.param("put", "/api/measurables/m1/scores/2026-11-02", {"value": "lots"}, "value",
                 "Score must be a number up to 11 digits, with up to 4 decimal places", id="score_not_a_number"),
]


@pytest.mark.parametrize(("method", "path", "body", "field", "message"), BAD_INPUTS)
def test_bad_input_gets_a_plain_message(sign_in, method, path, body, field, message):
    response = sign_in("u2").request(method, path, json=body)

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "invalid_input", "message": message, "fields": [{"field": field, "message": message}]}
    }


def test_several_bad_fields_keep_the_general_message(sign_in):
    response = sign_in("u2").post("/api/teams/team_lead/issues", json={"title": "", "priority": 0})

    assert response.json()["error"]["message"] == "Some fields are invalid"
    assert [field["field"] for field in response.json()["error"]["fields"]] == ["title", "priority"]


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
