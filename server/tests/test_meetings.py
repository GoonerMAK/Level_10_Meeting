import asyncio
from datetime import datetime, timedelta

import asyncpg
import pytest

from conftest import TEST_DATABASE_URL, execute_sql

START = "/api/teams/team_lead/meetings"
MEETING_TEST_ROWS = """
DELETE FROM meetings WHERE id NOT IN ('mt1', 'mt2');
DELETE FROM todos WHERE title LIKE 'Summary %';
DELETE FROM issues WHERE title LIKE 'Summary %';
"""


@pytest.fixture(autouse=True)
def remove_started_meetings():
    yield
    asyncio.run(execute_sql(MEETING_TEST_ROWS))


def at(value):
    return datetime.fromisoformat(value)


def start(sign_in, user_id):
    return sign_in(user_id).post(START)


def as_user(sign_in, user_id, method, url, **options):
    return sign_in(user_id).request(method, url, **options)


def test_starting_makes_you_the_facilitator_in_scorecard(sign_in, fixed_clock):
    response = start(sign_in, "u2")

    meeting = response.json()
    assert response.status_code == 201
    assert meeting["facilitator"] == {"id": "u2", "name": "Blake Brooks"}
    assert [attendee["id"] for attendee in meeting["attendees"]] == ["u2"]
    assert meeting["section"] == "scorecard"
    assert at(meeting["started_at"]) == at(meeting["section_started_at"]) == fixed_clock.now()
    assert at(meeting["section_ends_at"]) == fixed_clock.now() + timedelta(minutes=5)
    assert meeting["over_time"] is False
    assert at(meeting["server_now"]) == fixed_clock.now()


def test_a_second_start_joins_the_running_meeting(sign_in):
    first = start(sign_in, "u2").json()
    second = start(sign_in, "u3")

    assert second.status_code == 200
    assert second.json()["id"] == first["id"]
    assert second.json()["facilitator"]["id"] == "u2"
    assert [attendee["id"] for attendee in second.json()["attendees"]] == ["u2", "u3"]


@pytest.mark.anyio
async def test_starts_at_the_same_moment_make_one_meeting(signed_in_clients):
    users = ["u1", "u2", "u3", "u4"]
    async with signed_in_clients(*users) as clients:
        responses = await asyncio.gather(*(clients[user].post(START) for user in users))

    assert sorted(response.status_code for response in responses) == [200, 200, 200, 201]
    assert len({response.json()["id"] for response in responses}) == 1


def test_an_admin_can_start_on_a_team_they_are_not_in(sign_in):
    assert sign_in("u1").post("/api/teams/team_ops/meetings").status_code == 201


@pytest.mark.parametrize(
    ("user_id", "status", "message"),
    [
        ("u5", 403, "Observers can join meetings but cannot start them"),
        ("u6", 404, "Team not found"),
    ],
    ids=["observer", "team member of another team"],
)
def test_starting_is_refused(sign_in, user_id, status, message):
    response = start(sign_in, user_id)

    assert response.status_code == status
    assert response.json()["error"]["message"] == message


def test_observers_can_join_once(sign_in):
    meeting_id = start(sign_in, "u2").json()["id"]

    observer = as_user(sign_in, "u5", "POST", f"/api/meetings/{meeting_id}/join")
    rejoin = as_user(sign_in, "u5", "POST", f"/api/meetings/{meeting_id}/join")

    assert observer.status_code == rejoin.status_code == 200
    assert [attendee["id"] for attendee in rejoin.json()["attendees"]] == ["u2", "u5"]


def test_a_team_member_of_another_team_cannot_see_or_join_the_meeting(sign_in):
    meeting_id = start(sign_in, "u2").json()["id"]

    assert as_user(sign_in, "u6", "GET", f"/api/meetings/{meeting_id}").status_code == 404
    assert as_user(sign_in, "u6", "POST", f"/api/meetings/{meeting_id}/join").status_code == 404


def test_the_facilitator_moves_through_the_agenda(sign_in, fixed_clock):
    meeting_id = start(sign_in, "u2").json()["id"]
    fixed_clock.advance(timedelta(minutes=2))

    ids = as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting_id}/next", json={"from_section": "scorecard"})
    conclude = as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting_id}/next", json={"from_section": "ids"})

    assert ids.json()["section"] == "ids"
    assert at(ids.json()["section_ends_at"]) == fixed_clock.now() + timedelta(minutes=60)
    assert conclude.json()["section"] == "conclude"
    assert at(conclude.json()["section_ends_at"]) == fixed_clock.now() + timedelta(minutes=10)


@pytest.mark.parametrize("user_id", ["u1", "u3", "u5"], ids=["admin", "team member", "observer"])
def test_only_the_facilitator_moves_on_or_ends(sign_in, user_id):
    meeting_id = start(sign_in, "u2").json()["id"]
    as_user(sign_in, user_id, "POST", f"/api/meetings/{meeting_id}/join")

    moved = as_user(sign_in, user_id, "POST", f"/api/meetings/{meeting_id}/next", json={"from_section": "scorecard"})
    ended = as_user(sign_in, user_id, "POST", f"/api/meetings/{meeting_id}/end")

    assert moved.status_code == ended.status_code == 403
    assert moved.json()["error"]["message"] == "Only the facilitator can move the meeting on or end it"


def test_an_old_section_does_not_move_the_meeting_twice(sign_in):
    meeting_id = start(sign_in, "u2").json()["id"]
    url = f"/api/meetings/{meeting_id}/next"
    as_user(sign_in, "u2", "POST", url, json={"from_section": "scorecard"})

    repeat = as_user(sign_in, "u2", "POST", url, json={"from_section": "scorecard"})

    assert repeat.status_code == 409
    assert repeat.json()["error"]["message"] == "The meeting has already moved on"
    assert as_user(sign_in, "u2", "GET", f"/api/meetings/{meeting_id}").json()["section"] == "ids"


@pytest.mark.anyio
async def test_two_next_clicks_at_once_move_one_section(signed_in_clients):
    async with signed_in_clients("u2") as clients:
        meeting_id = (await clients["u2"].post(START)).json()["id"]
        url = f"/api/meetings/{meeting_id}/next"
        clicks = await asyncio.gather(*(clients["u2"].post(url, json={"from_section": "scorecard"}) for _ in range(2)))
        meeting = (await clients["u2"].get(f"/api/meetings/{meeting_id}")).json()

    assert sorted(click.status_code for click in clicks) == [200, 409]
    assert meeting["section"] == "ids"


def test_conclude_is_the_last_section(sign_in):
    meeting_id = start(sign_in, "u2").json()["id"]
    url = f"/api/meetings/{meeting_id}/next"
    for section in ("scorecard", "ids"):
        as_user(sign_in, "u2", "POST", url, json={"from_section": section})

    response = as_user(sign_in, "u2", "POST", url, json={"from_section": "conclude"})

    assert response.status_code == 409
    assert response.json()["error"]["message"] == "Conclude is the last section. End the meeting instead"


def test_an_overrun_shows_as_over_time_and_does_not_move_on(sign_in, fixed_clock):
    meeting_id = start(sign_in, "u2").json()["id"]
    url = f"/api/meetings/{meeting_id}"

    fixed_clock.advance(timedelta(minutes=5))
    on_the_minute = as_user(sign_in, "u3", "GET", url).json()
    fixed_clock.advance(timedelta(seconds=1))
    a_second_over = as_user(sign_in, "u3", "GET", url).json()

    assert (on_the_minute["section"], on_the_minute["over_time"]) == ("scorecard", False)
    assert (a_second_over["section"], a_second_over["over_time"]) == ("scorecard", True)


def test_the_facilitator_can_end_at_any_time(sign_in, fixed_clock):
    meeting_id = start(sign_in, "u2").json()["id"]
    fixed_clock.advance(timedelta(minutes=1))

    ended = as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting_id}/end").json()

    assert at(ended["ended_at"]) == fixed_clock.now()
    assert (ended["section"], ended["section_ends_at"], ended["over_time"]) == (None, None, False)


def test_a_clock_set_back_still_moves_on_and_ends_after_the_start(sign_in, fixed_clock):
    meeting = start(sign_in, "u2").json()
    fixed_clock.advance(timedelta(days=-7))

    moved = as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting['id']}/next", json={"from_section": "scorecard"})
    ended = as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting['id']}/end")

    assert moved.status_code == ended.status_code == 200
    assert at(moved.json()["section_started_at"]) == at(meeting["started_at"])
    assert at(ended.json()["ended_at"]) == at(meeting["started_at"])


@pytest.mark.anyio
async def test_a_join_that_waits_on_the_end_is_refused(signed_in_clients):
    async with signed_in_clients("u2", "u5") as clients:
        meeting_id = (await clients["u2"].post(START)).json()["id"]
        ending = await asyncpg.connect(TEST_DATABASE_URL.set(drivername="postgresql").render_as_string(hide_password=False))
        try:
            async with ending.transaction():
                await ending.execute("SELECT 1 FROM meetings WHERE id = $1 FOR UPDATE", meeting_id)
                join = asyncio.create_task(clients["u5"].post(f"/api/meetings/{meeting_id}/join"))
                await asyncio.sleep(0.3)
                await ending.execute(
                    "UPDATE meetings SET ended_at = started_at, current_section = NULL, section_started_at = NULL "
                    "WHERE id = $1",
                    meeting_id,
                )
            joined = await join
        finally:
            await ending.close()
        meeting = (await clients["u2"].get(f"/api/meetings/{meeting_id}")).json()

    assert joined.status_code == 409
    assert joined.json()["error"]["message"] == "This meeting has already ended"
    assert [attendee["id"] for attendee in meeting["attendees"]] == ["u2"]


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [("POST", "end", None), ("POST", "join", None), ("POST", "next", {"from_section": "scorecard"})],
    ids=["end again", "join", "next"],
)
def test_an_ended_meeting_refuses_changes(sign_in, method, path, body):
    meeting_id = start(sign_in, "u2").json()["id"]
    as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting_id}/end")

    response = as_user(sign_in, "u2", method, f"/api/meetings/{meeting_id}/{path}", json=body)

    assert response.status_code == 409
    assert response.json()["error"]["message"] == "This meeting has already ended"


def test_after_the_end_a_new_meeting_can_start(sign_in):
    first = start(sign_in, "u2").json()["id"]
    as_user(sign_in, "u2", "POST", f"/api/meetings/{first}/end")

    assert as_user(sign_in, "u3", "GET", "/api/teams/team_lead/meetings/active").status_code == 404
    second = start(sign_in, "u3")
    assert second.status_code == 201
    assert second.json()["id"] != first


def test_a_late_join_or_refresh_gets_the_current_state(sign_in):
    meeting_id = start(sign_in, "u2").json()["id"]
    as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting_id}/next", json={"from_section": "scorecard"})

    active = as_user(sign_in, "u4", "GET", "/api/teams/team_lead/meetings/active").json()

    assert (active["id"], active["section"]) == (meeting_id, "ids")


def test_a_seeded_meeting_reads_as_ended(sign_in):
    response = as_user(sign_in, "u2", "GET", "/api/meetings/mt1").json()

    assert response["ended_at"] == "2026-10-28T16:15:00Z"
    assert response["section"] is None
    assert [attendee["id"] for attendee in response["attendees"]] == ["u1", "u2", "u3", "u4", "u5"]


def in_conclude(sign_in, *attendees):
    meeting_id = start(sign_in, "u2").json()["id"]
    for user_id in attendees:
        as_user(sign_in, user_id, "POST", f"/api/meetings/{meeting_id}/join")
    for section in ("scorecard", "ids"):
        as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting_id}/next", json={"from_section": section})
    return meeting_id


def rate(sign_in, user_id, meeting_id, rating):
    return as_user(sign_in, user_id, "PUT", f"/api/meetings/{meeting_id}/rating", json={"rating": rating})


def test_attendees_rate_in_conclude_and_can_change_it(sign_in):
    meeting_id = in_conclude(sign_in, "u1")
    rate(sign_in, "u2", meeting_id, 7)
    rate(sign_in, "u1", meeting_id, 10)

    changed = rate(sign_in, "u2", meeting_id, 9)

    assert changed.status_code == 200
    assert changed.json()["ratings"] == [
        {"user": {"id": "u1", "name": "Avery Admin"}, "rating": 10},
        {"user": {"id": "u2", "name": "Blake Brooks"}, "rating": 9},
    ]
    assert changed.json()["rating"] == 9.5


@pytest.mark.parametrize(
    ("user_id", "status", "message"),
    [
        ("u5", 403, "Observers can follow the meeting but cannot rate it"),
        ("u3", 403, "Join the meeting before rating it"),
        ("u6", 404, "Meeting not found"),
    ],
    ids=["observer", "not attending", "other team"],
)
def test_rating_is_refused_for(sign_in, user_id, status, message):
    meeting_id = in_conclude(sign_in, "u5")

    response = rate(sign_in, user_id, meeting_id, 8)

    assert response.status_code == status
    assert response.json()["error"]["message"] == message


def test_ratings_open_only_in_conclude(sign_in):
    meeting_id = start(sign_in, "u2").json()["id"]

    response = rate(sign_in, "u2", meeting_id, 8)

    assert response.status_code == 409
    assert response.json()["error"]["message"] == "Ratings open in Conclude"


def test_ratings_close_when_the_meeting_ends(sign_in):
    meeting_id = in_conclude(sign_in)
    rate(sign_in, "u2", meeting_id, 8)
    as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting_id}/end")

    response = rate(sign_in, "u2", meeting_id, 3)

    assert response.status_code == 409
    assert as_user(sign_in, "u2", "GET", f"/api/meetings/{meeting_id}").json()["ratings"][0]["rating"] == 8


@pytest.mark.parametrize("rating", [0, 11])
def test_a_rating_outside_1_to_10_is_invalid(sign_in, rating):
    meeting_id = in_conclude(sign_in)

    assert rate(sign_in, "u2", meeting_id, rating).status_code == 422


def test_a_seeded_meeting_lists_its_ratings(sign_in):
    ratings = as_user(sign_in, "u2", "GET", "/api/meetings/mt2").json()["ratings"]

    assert [(entry["user"]["id"], entry["rating"]) for entry in ratings] == [("u1", 8), ("u2", 9), ("u3", 8), ("u4", 8)]


SEEDED_SUMMARIES = {
    "mt1": {
        "scorecard_week": "2026-10-19",
        "statuses": {"m1": "on_track", "m2": "on_track", "m3": "on_track", "m4": "on_track", "m5": "off_track"},
        "issues_solved": ["i7"],
        "todos_created": ["t20"],
        "rating": 8.0,
    },
    "mt2": {
        "scorecard_week": "2026-10-26",
        "statuses": {"m1": "off_track", "m2": "on_track", "m3": "on_track", "m4": "off_track", "m5": "on_track"},
        "issues_solved": ["i6"],
        "todos_created": ["t30"],
        "rating": 8.3,
    },
}


def summary_of(sign_in, user_id, meeting_id):
    return as_user(sign_in, user_id, "GET", f"/api/meetings/{meeting_id}/summary")


def new_issue(sign_in, title):
    return as_user(sign_in, "u2", "POST", "/api/teams/team_lead/issues", json={"title": title}).json()["id"]


def new_todo(sign_in, issue_id, title):
    return as_user(sign_in, "u2", "POST", f"/api/issues/{issue_id}/todos", json={"title": title, "owner_id": "u2"})


def solve(sign_in, issue_id):
    return as_user(sign_in, "u2", "POST", f"/api/issues/{issue_id}/solve", json={"resolution_note": "Agreed"})


@pytest.mark.parametrize("meeting_id", ["mt1", "mt2"])
def test_a_seeded_meeting_summary_matches_the_seed(sign_in, meeting_id):
    expected = SEEDED_SUMMARIES[meeting_id]

    response = summary_of(sign_in, "u5", meeting_id)

    summary = response.json()
    assert response.status_code == 200
    assert summary["scorecard_week"] == expected["scorecard_week"]
    assert {row["id"]: row["status"] for row in summary["measurables"]} == expected["statuses"]
    assert [issue["id"] for issue in summary["issues_solved"]] == expected["issues_solved"]
    assert [todo["id"] for todo in summary["todos_created"]] == expected["todos_created"]
    assert sorted(attendee["id"] for attendee in summary["attendees"]) == ["u1", "u2", "u3", "u4", "u5"]
    assert summary["rating"] == expected["rating"]


def test_a_summary_counts_what_happened_from_the_start_to_the_end(sign_in, fixed_clock):
    discussed = new_issue(sign_in, "Summary discussed")
    new_todo(sign_in, discussed, "Summary before the start")
    fixed_clock.advance(timedelta(seconds=1))
    meeting_id = start(sign_in, "u2").json()["id"]
    new_todo(sign_in, discussed, "Summary at the start")
    fixed_clock.advance(timedelta(minutes=10))
    solve(sign_in, discussed)
    new_todo(sign_in, discussed, "Summary at the end")
    as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting_id}/end")
    fixed_clock.advance(timedelta(seconds=1))
    late = new_issue(sign_in, "Summary after the end")
    new_todo(sign_in, late, "Summary after the end")
    solve(sign_in, late)

    summary = summary_of(sign_in, "u2", meeting_id).json()

    assert summary["scorecard_week"] == "2026-11-02"
    assert [issue["id"] for issue in summary["issues_solved"]] == [discussed]
    assert [todo["title"] for todo in summary["todos_created"]] == ["Summary at the start", "Summary at the end"]
    assert summary["todos_created"][0]["owner"] == {"id": "u2", "name": "Blake Brooks"}
    assert [attendee["id"] for attendee in summary["attendees"]] == ["u2"]


def test_a_meeting_nobody_rated_has_no_score(sign_in):
    meeting_id = in_conclude(sign_in)
    as_user(sign_in, "u2", "POST", f"/api/meetings/{meeting_id}/end")

    summary = summary_of(sign_in, "u2", meeting_id).json()

    assert (summary["rating"], summary["ratings"]) == (None, [])


def test_a_running_meeting_summarises_what_happened_so_far(sign_in, fixed_clock):
    discussed = new_issue(sign_in, "Summary so far")
    fixed_clock.advance(timedelta(seconds=1))
    meeting_id = start(sign_in, "u2").json()["id"]
    new_todo(sign_in, discussed, "Summary so far, first")
    fixed_clock.advance(timedelta(minutes=1))
    new_todo(sign_in, discussed, "Summary so far, second")

    response = summary_of(sign_in, "u2", meeting_id)

    summary = response.json()
    assert response.status_code == 200
    assert summary["ended_at"] is None
    assert [todo["title"] for todo in summary["todos_created"]] == ["Summary so far, first", "Summary so far, second"]


def test_a_team_member_of_another_team_cannot_read_the_summary(sign_in):
    assert summary_of(sign_in, "u6", "mt1").status_code == 404
