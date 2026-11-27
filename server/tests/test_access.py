import asyncio

import pytest

from conftest import execute_sql

PAGES = ("scorecard", "issues", "todos", "rocks")
CURRENT_WEEK = "2026-11-09"
FIRST_OF_13_WEEKS = "2026-08-17"
SEEDED_FIRST_WEEK_SCORE = 12
ACCESS_TEST_ROWS = f"""
DELETE FROM todos WHERE id !~ '^t[0-9]+$';
DELETE FROM issues WHERE id !~ '^i[0-9]+$';
DELETE FROM scores WHERE week_start = '{CURRENT_WEEK}' AND measurable_id IN ('m1', 'm6', 'm7');
UPDATE scores SET value = {SEEDED_FIRST_WEEK_SCORE}, updated_by_id = NULL
WHERE measurable_id = 'm1' AND week_start = '{FIRST_OF_13_WEEKS}';
"""

WRITES_ON_LEADERSHIP = [
    pytest.param("PUT", "/api/measurables/m1/scores/2026-11-02", {"value": 5}, id="score"),
    pytest.param("POST", "/api/measurables/m1/scores/2026-10-05/issue", None, id="make it an issue"),
    pytest.param("POST", "/api/teams/team_lead/issues", {"title": "Access check"}, id="create issue"),
    pytest.param("PATCH", "/api/issues/i1", {"priority": 3}, id="priority"),
    pytest.param("POST", "/api/issues/i1/solve", {"resolution_note": "Agreed"}, id="solve"),
    pytest.param("POST", "/api/issues/i1/todos", {"title": "Access check", "owner_id": "u2"}, id="add to-do"),
    pytest.param("POST", "/api/todos/t12/done", None, id="done"),
    pytest.param("POST", "/api/todos/t12/undo", None, id="undo"),
]
REFUSED_WRITERS = [
    pytest.param("u5", 403, "forbidden", id="observer on the team"),
    pytest.param("u7", 404, "not_found", id="observer of another team"),
    pytest.param("u6", 404, "not_found", id="sales team member"),
    pytest.param("u8", 404, "not_found", id="operations team member"),
]
OUTSIDERS = [
    pytest.param("u6", "team_lead", id="sales member on leadership"),
    pytest.param("u3", "team_sales", id="leadership member on sales"),
    pytest.param("u8", "team_lead", id="operations member on leadership"),
    pytest.param("u7", "team_ops", id="sales observer on operations"),
]
ACTORS = [
    pytest.param("u2", "team_lead", "m1", "2026-10-05", id="team member on their team"),
    pytest.param("u1", "team_sales", "m6", "2026-10-12", id="admin not on sales"),
    pytest.param("u1", "team_ops", "m7", "2026-10-12", id="admin not on operations"),
]


@pytest.fixture(autouse=True)
def remove_access_test_rows():
    yield
    asyncio.run(execute_sql(ACCESS_TEST_ROWS))


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize(("user_id", "team_id"), OUTSIDERS)
def test_another_teams_data_is_refused(sign_in, user_id, team_id, page):
    response = sign_in(user_id).get(f"/api/teams/{team_id}/{page}")

    assert (response.status_code, response.json()["error"]["code"]) == (404, "not_found")


@pytest.mark.parametrize("page", PAGES)
def test_an_observer_reads_their_team(sign_in, page):
    assert sign_in("u5").get(f"/api/teams/team_lead/{page}").status_code == 200


@pytest.mark.parametrize(("user_id", "status", "code"), REFUSED_WRITERS)
@pytest.mark.parametrize(("method", "url", "body"), WRITES_ON_LEADERSHIP)
def test_writes_are_refused_for_observers_and_other_teams(sign_in, user_id, status, code, method, url, body):
    response = sign_in(user_id).request(method, url, json=body)

    assert (response.status_code, response.json()["error"]["code"]) == (status, code)


def test_a_guessed_id_on_another_team_looks_like_a_missing_one(sign_in):
    guessed = sign_in("u6").patch("/api/issues/i1", json={"priority": 3})
    missing = sign_in("u6").patch("/api/issues/no-such-issue", json={"priority": 3})

    assert guessed.status_code == missing.status_code == 404
    assert guessed.json() == missing.json() == {"error": {"code": "not_found", "message": "Issue not found"}}


@pytest.mark.parametrize(("user_id", "team_id", "measurable_id", "off_track_week"), ACTORS)
def test_every_action_works(sign_in, user_id, team_id, measurable_id, off_track_week):
    user = sign_in(user_id)
    reads = [user.get(f"/api/teams/{team_id}/{page}").status_code for page in PAGES]
    score = user.put(f"/api/measurables/{measurable_id}/scores/{CURRENT_WEEK}", json={"value": 7})
    issue = user.post(f"/api/teams/{team_id}/issues", json={"title": "Access check"})
    issue_url = f"/api/issues/{issue.json()['id']}"
    prioritised = user.patch(issue_url, json={"priority": 5})
    cleared = user.patch(issue_url, json={"priority": None})
    todo = user.post(f"{issue_url}/todos", json={"title": "Access check", "owner_id": user_id})
    done = user.post(f"/api/todos/{todo.json()['id']}/done")
    undone = user.post(f"/api/todos/{todo.json()['id']}/undo")
    solved = user.post(f"{issue_url}/solve", json={"resolution_note": "Agreed"})
    solved_again = user.post(f"{issue_url}/solve", json={"resolution_note": "Agreed"})
    from_score = user.post(f"/api/measurables/{measurable_id}/scores/{off_track_week}/issue")

    assert reads == [200, 200, 200, 200]
    assert (score.status_code, score.json()["value"]) == (200, 7)
    assert (issue.status_code, issue.json()["owner"]["id"]) == (201, user_id)
    assert (prioritised.json()["priority"], cleared.json()["priority"]) == (5, None)
    assert (todo.status_code, todo.json()["owner"]["id"]) == (201, user_id)
    assert (done.json()["done_at"] is not None, undone.json()["done_at"]) == (True, None)
    assert (solved.status_code, solved.json()["resolution_note"]) == (200, "Agreed")
    assert (solved_again.status_code, solved_again.json()["error"]["code"]) == (409, "conflict")
    assert (from_score.status_code, from_score.json()["source"]["week_start"]) == (201, off_track_week)


def test_the_first_of_the_13_weeks_takes_a_score(sign_in):
    response = sign_in("u2").put(f"/api/measurables/m1/scores/{FIRST_OF_13_WEEKS}", json={"value": 9})

    assert (response.status_code, response.json()["value"]) == (200, 9)
