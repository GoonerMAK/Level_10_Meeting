import asyncio

import pytest
from conftest import execute_sql


def activity(client, team_id, entity_id, **params):
    response = client.get(f"/api/teams/{team_id}/activity", params={"limit": 200, **params})
    assert response.status_code == 200
    return [entry for entry in response.json() if entry["entity_id"] == entity_id]


def summary(entries):
    return [(entry["action"], entry["user"]["id"] if entry["user"] else None, entry["changes"]) for entry in entries]


@pytest.fixture
def cleanup():
    statements = []
    yield statements.append
    asyncio.run(execute_sql(";".join(statements)))


def test_score_changes_are_recorded_with_before_and_after(sign_in, cleanup):
    cleanup("DELETE FROM scores WHERE measurable_id = 'm1' AND week_start = '2026-11-09'")
    cleanup("DELETE FROM activity_logs WHERE entity_id = 'm1:2026-11-09'")
    user = sign_in("u2")
    user.put("/api/measurables/m1/scores/2026-11-09", json={"value": 7})
    user.put("/api/measurables/m1/scores/2026-11-09", json={"value": 8.5})

    entries = activity(user, "team_lead", "m1:2026-11-09")

    assert summary(entries) == [
        ("updated", "u2", [{"field": "value", "before": "7", "after": "8.5"}]),
        ("created", "u2", [{"field": "value", "before": None, "after": "7"}]),
    ]
    assert entries[0]["entity_label"] == "New deals closed, week of Nov 9"
    assert entries[0]["user"] == {"id": "u2", "name": "Blake Brooks"}


def test_an_issue_and_its_todo_are_traced_from_creation_to_done(sign_in, cleanup):
    user = sign_in("u2")
    issue_id = user.post("/api/teams/team_lead/issues", json={"title": "Audit check"}).json()["id"]
    cleanup(f"DELETE FROM activity_logs WHERE entity_id = '{issue_id}' OR team_id = 'team_lead' AND entity = 'todo' AND entity_label = 'Follow up'")
    cleanup(f"DELETE FROM todos WHERE source_issue_id = '{issue_id}'")
    cleanup(f"DELETE FROM issues WHERE id = '{issue_id}'")
    user.patch(f"/api/issues/{issue_id}", json={"priority": 4})
    todo_id = user.post(f"/api/issues/{issue_id}/todos", json={"title": "Follow up", "owner_id": "u3"}).json()["id"]
    user.post(f"/api/todos/{todo_id}/done")
    user.post(f"/api/todos/{todo_id}/undo")
    user.post(f"/api/issues/{issue_id}/solve", json={"resolution_note": "Checked"})

    assert [action for action, _, _ in summary(activity(user, "team_lead", issue_id))] == ["solved", "updated", "created"]
    assert summary(activity(user, "team_lead", issue_id))[1][2] == [{"field": "priority", "before": None, "after": 4}]
    todo_entries = activity(user, "team_lead", todo_id)
    assert [action for action, _, _ in summary(todo_entries)] == ["updated", "updated", "created"]
    assert todo_entries[0]["changes"][0]["after"] is None
    assert todo_entries[1]["changes"][0]["before"] is None


def test_a_meeting_is_traced_from_start_to_end(sign_in, cleanup):
    user = sign_in("u8")
    meeting_id = user.post("/api/teams/team_ops/meetings").json()["id"]
    cleanup(f"DELETE FROM activity_logs WHERE entity_id = '{meeting_id}'")
    cleanup(f"DELETE FROM meetings WHERE id = '{meeting_id}'")
    user.post(f"/api/meetings/{meeting_id}/next", json={"from_section": "scorecard"})
    user.post(f"/api/meetings/{meeting_id}/end")

    assert summary(activity(user, "team_ops", meeting_id)) == [
        ("updated", "u8", [{"field": "section", "before": "ids", "after": None}]),
        ("updated", "u8", [{"field": "section", "before": "scorecard", "after": "ids"}]),
        ("updated", "u8", [{"field": "attendee", "before": None, "after": "u8"}]),
        ("created", "u8", [{"field": "section", "before": None, "after": "scorecard"}]),
    ]


def test_activity_pages_newest_first(sign_in, cleanup):
    cleanup("DELETE FROM scores WHERE measurable_id = 'm7' AND week_start = '2026-11-09'")
    cleanup("DELETE FROM activity_logs WHERE entity_id = 'm7:2026-11-09'")
    user = sign_in("u8")
    for value in (1, 2, 3):
        user.put("/api/measurables/m7/scores/2026-11-09", json={"value": value})
    newest = user.get("/api/teams/team_ops/activity", params={"limit": 1}).json()
    older = user.get("/api/teams/team_ops/activity", params={"limit": 2, "before_id": newest[0]["id"]}).json()

    assert [entry["changes"][0]["after"] for entry in newest + older] == ["3", "2", "1"]


def test_another_teams_activity_is_refused(sign_in):
    response = sign_in("u2").get("/api/teams/team_ops/activity")

    assert response.status_code == 404
