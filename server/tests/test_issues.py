def test_observer_write_is_refused(client):
    response = client.post("/api/teams/team_lead/issues", headers={"X-User-Id": "u5"}, json={"title": "Hiring plan"})

    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "forbidden", "message": "Observers can view this team but cannot change anything"}
    }
