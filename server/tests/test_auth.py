import json
from base64 import b64encode

import pytest
from itsdangerous import TimestampSigner

from app.modules.auth import service

DAY = 24 * 60 * 60
SIGNED_IN_AT = 1_800_000_000


def cookie_signed_with_another_secret(user_id):
    payload = b64encode(json.dumps({"user_id": user_id}).encode())
    return TimestampSigner("another-secret").sign(payload).decode()


def test_users_list_opens_without_signing_in(client):
    response = client.get("/api/auth/users")

    assert response.status_code == 200
    users = response.json()
    assert [user["id"] for user in users] == ["u1", "u2", "u3", "u4", "u5", "u6", "u7", "u8", "u9"]
    assert users[1] == {
        "id": "u2",
        "name": "Blake Brooks",
        "role": "team_member",
        "teams": [{"id": "team_lead", "name": "Leadership"}, {"id": "team_sales", "name": "Sales"}],
    }


def test_sign_in_remembers_the_user(client):
    signed_in = client.post("/api/auth/sign-in", json={"user_id": "u2"})
    me = client.get("/api/auth/me")

    assert signed_in.status_code == 200
    assert me.json() == signed_in.json() == {
        "id": "u2",
        "name": "Blake Brooks",
        "email": "blake@acme.test",
        "role": "team_member",
        "team_ids": ["team_lead", "team_sales"],
    }


def test_sign_in_cookie_is_hidden_from_page_scripts_and_lasts_3_idle_days(client):
    response = client.post("/api/auth/sign-in", json={"user_id": "u2"})

    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "max-age=259200" in cookie


def test_signing_in_as_another_user_switches(sign_in):
    client = sign_in("u2")
    client.post("/api/auth/sign-in", json={"user_id": "u5"})

    assert client.get("/api/auth/me").json()["id"] == "u5"


def test_sign_in_as_an_unknown_user_is_invalid(client):
    response = client.post("/api/auth/sign-in", json={"user_id": "u99"})

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "invalid_input",
            "message": "Unknown user",
            "fields": [{"field": "user_id", "message": "Unknown user"}],
        }
    }


def test_signing_out_forgets_the_user(sign_in):
    client = sign_in("u2")
    signed_out = client.post("/api/auth/sign-out")

    assert signed_out.status_code == 204
    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize(
    ("headers", "cookie"),
    [
        ({}, None),
        ({"X-User-Id": "u1"}, None),
        ({}, "forged"),
        ({}, cookie_signed_with_another_secret("u1")),
    ],
    ids=["nothing", "sent user id", "forged cookie", "cookie signed with another secret"],
)
def test_only_a_signed_in_user_is_known(client, headers, cookie):
    client.cookies.clear()
    if cookie:
        client.cookies.set("session", cookie)
    response = client.get("/api/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.json() == {"error": {"code": "unauthorized", "message": "Choose a user first"}}


@pytest.fixture
def clock(monkeypatch):
    now = {"seconds": SIGNED_IN_AT}
    monkeypatch.setattr(service, "now_seconds", lambda: now["seconds"])
    monkeypatch.setattr(TimestampSigner, "get_timestamp", lambda _signer: now["seconds"])

    def move_to(seconds_after_sign_in):
        now["seconds"] = SIGNED_IN_AT + seconds_after_sign_in

    return move_to


def me_status_at(client, clock, seconds_after_sign_in):
    clock(seconds_after_sign_in)
    return client.get("/api/auth/me").status_code


def test_using_the_app_keeps_the_sign_in_alive(sign_in, clock):
    client = sign_in("u2")

    assert me_status_at(client, clock, 2 * DAY) == 200
    assert me_status_at(client, clock, 4 * DAY) == 200


def test_sign_in_ends_after_3_idle_days(sign_in, clock):
    client = sign_in("u2")

    assert me_status_at(client, clock, 3 * DAY + 1) == 401


def test_sign_in_ends_7_days_after_signing_in_even_when_active(sign_in, clock):
    client = sign_in("u2")

    assert [me_status_at(client, clock, day * DAY) for day in (2, 4, 6)] == [200, 200, 200]
    assert me_status_at(client, clock, 7 * DAY + 1) == 401


def test_sign_in_renews_at_most_once_an_hour(sign_in, clock):
    client = sign_in("u2")
    clock(30 * 60)

    assert "set-cookie" not in client.get("/api/auth/me").headers
    clock(2 * 60 * 60)
    assert "set-cookie" in client.get("/api/auth/me").headers
