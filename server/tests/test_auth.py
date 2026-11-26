import pytest


def test_current_user_is_loaded_with_their_teams(client):
    response = client.get("/api/auth/me", headers={"X-User-Id": "u2"})

    assert response.status_code == 200
    assert response.json() == {
        "id": "u2",
        "name": "Blake Brooks",
        "email": "blake@acme.test",
        "role": "team_member",
        "team_ids": ["team_lead", "team_sales"],
    }


@pytest.mark.parametrize(
    ("headers", "message"),
    [({}, "Choose a user first"), ({"X-User-Id": "u99"}, "Unknown user")],
)
def test_missing_or_unknown_user_is_unauthorized(client, headers, message):
    response = client.get("/api/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.json() == {"error": {"code": "unauthorized", "message": message}}
