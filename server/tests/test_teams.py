def team_names(sign_in, user_id):
    response = sign_in(user_id).get("/api/teams")
    assert response.status_code == 200
    return [team["name"] for team in response.json()]


def test_team_member_sees_only_their_teams(sign_in):
    assert team_names(sign_in, "u2") == ["Leadership", "Sales"]


def test_admin_sees_every_team(sign_in):
    assert team_names(sign_in, "u1") == ["Leadership", "Operations", "Sales"]


def test_team_member_reading_another_team_is_refused(sign_in):
    response = sign_in("u2").get("/api/teams/team_ops")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Team not found"}}


def test_todo_owners_are_the_team_members_then_every_admin(sign_in):
    response = sign_in("u6").get("/api/teams/team_sales")

    assert response.status_code == 200
    assert response.json()["todo_owners"] == [
        {"id": "u2", "name": "Blake Brooks", "role": "team_member", "on_team": True},
        {"id": "u6", "name": "Finley Ford", "role": "team_member", "on_team": True},
        {"id": "u1", "name": "Avery Admin", "role": "admin", "on_team": False},
    ]


def test_an_admin_on_the_team_is_marked_on_team(sign_in):
    owners = sign_in("u2").get("/api/teams/team_lead").json()["todo_owners"]

    assert {"id": "u1", "name": "Avery Admin", "role": "admin", "on_team": True} in owners
    assert "u5" not in [owner["id"] for owner in owners]
