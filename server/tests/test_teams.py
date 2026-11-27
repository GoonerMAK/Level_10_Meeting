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
