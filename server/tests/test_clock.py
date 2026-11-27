import time


def test_today_stays_on_the_app_now_date_while_the_server_runs(sign_in, monkeypatch):
    a_week_of_uptime = time.monotonic() - 7 * 24 * 60 * 60
    monkeypatch.setattr("app.core.clock.STARTED_AT", a_week_of_uptime)

    response = sign_in("u2").get("/api/teams/team_lead/scorecard")

    assert response.status_code == 200
    assert response.json()["current_week"] == "2026-11-09"
