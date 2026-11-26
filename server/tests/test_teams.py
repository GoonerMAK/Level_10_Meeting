def team_names(client, user_id):
    response = client.get("/api/teams", headers={"X-User-Id": user_id})
    assert response.status_code == 200
    return [team["name"] for team in response.json()]


def test_team_member_sees_only_their_teams(client):
    assert team_names(client, "u2") == ["Leadership", "Sales"]


def test_admin_sees_every_team(client):
    assert team_names(client, "u1") == ["Leadership", "Operations", "Sales"]


def test_team_member_reading_another_team_is_refused(client):
    response = client.get("/api/teams/team_ops", headers={"X-User-Id": "u2"})

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Team not found"}}
