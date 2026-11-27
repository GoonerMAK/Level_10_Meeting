import asyncio

import pytest
from starlette.websockets import WebSocketDisconnect

from conftest import execute_sql

WEB_APP = {"origin": "http://localhost:3000"}
LEAD = "/api/live?team_id=team_lead"
START = "/api/teams/team_lead/meetings"


LIVE_TEST_ROWS = """
DELETE FROM meetings WHERE id NOT IN ('mt1', 'mt2');
DELETE FROM scores WHERE measurable_id = 'm1' AND week_start = '2026-11-09';
DELETE FROM todos WHERE title = 'Call the client';
DELETE FROM issues WHERE title = 'Hiring plan';
"""


@pytest.fixture(autouse=True)
def remove_live_test_rows():
    yield
    asyncio.run(execute_sql(LIVE_TEST_ROWS))


def connect(sign_in, user_id, url=LEAD):
    live = sign_in(user_id).websocket_connect(url, headers=WEB_APP)
    return live


def opened(live):
    hello = live.receive_json()
    meeting = live.receive_json()
    return hello, meeting


def section_of(message):
    return message["meeting"]["section"]


def test_connecting_says_who_you_are_and_sends_the_meeting(sign_in):
    with connect(sign_in, "u2") as live:
        hello, meeting = opened(live)

    assert hello == {"type": "hello", "user": {"id": "u2", "name": "Blake Brooks"}}
    assert meeting == {"type": "meeting", "meeting": None}


@pytest.mark.parametrize(
    ("user_id", "url", "headers", "reason"),
    [
        (None, LEAD, WEB_APP, "Choose a user first"),
        ("u2", LEAD, {"origin": "https://evil.example"}, "Unknown web address"),
        ("u2", LEAD, {}, "Unknown web address"),
        ("u6", LEAD, WEB_APP, "Team not found"),
        ("u1", "/api/live?team_id=team_nope", WEB_APP, "Team not found"),
    ],
    ids=["not signed in", "other web address", "no web address", "other team", "unknown team"],
)
def test_live_connection_is_refused(client, sign_in, user_id, url, headers, reason):
    if user_id:
        sign_in(user_id)
    with pytest.raises(WebSocketDisconnect) as refused:
        with client.websocket_connect(url, headers=headers):
            pass

    assert (refused.value.code, refused.value.reason) == (1008, reason)


def test_two_connections_follow_the_facilitator(sign_in):
    with connect(sign_in, "u3") as follower, connect(sign_in, "u4") as late:
        opened(follower)
        opened(late)
        meeting_id = sign_in("u2").post(START).json()["id"]
        started = [follower.receive_json(), late.receive_json()]
        sign_in("u2").post(f"/api/meetings/{meeting_id}/next", json={"from_section": "scorecard"})
        moved = [follower.receive_json(), late.receive_json()]

    assert [section_of(message) for message in started] == ["scorecard", "scorecard"]
    assert [section_of(message) for message in moved] == ["ids", "ids"]
    assert moved[0]["meeting"]["section_ends_at"] == moved[1]["meeting"]["section_ends_at"]


def test_a_join_shows_up_once(sign_in):
    meeting_id = sign_in("u2").post(START).json()["id"]
    with connect(sign_in, "u3") as live:
        opened(live)
        sign_in("u5").post(f"/api/meetings/{meeting_id}/join")
        joined = live.receive_json()
        sign_in("u5").post(f"/api/meetings/{meeting_id}/join")
        sign_in("u2").post(f"/api/meetings/{meeting_id}/next", json={"from_section": "scorecard"})
        after_rejoin = live.receive_json()

    assert [attendee["id"] for attendee in joined["meeting"]["attendees"]] == ["u2", "u5"]
    assert section_of(after_rejoin) == "ids"


@pytest.mark.parametrize(
    ("method", "url", "body", "what"),
    [
        ("PUT", "/api/measurables/m1/scores/2026-11-09", {"value": 7}, "scorecard"),
        ("POST", "/api/teams/team_lead/issues", {"title": "Hiring plan"}, "issues"),
        ("POST", "/api/issues/i5/todos", {"title": "Call the client", "owner_id": "u2"}, "todos"),
    ],
    ids=["score", "issue", "to-do"],
)
def test_team_page_edits_reach_the_live_connection(sign_in, method, url, body, what):
    with connect(sign_in, "u3") as live:
        opened(live)
        response = sign_in("u2").request(method, url, json=body)
        message = live.receive_json()

    assert response.status_code < 300
    assert message == {"type": "changed", "what": what}


def test_a_reconnect_gets_the_current_state(sign_in):
    meeting_id = sign_in("u2").post(START).json()["id"]
    sign_in("u2").post(f"/api/meetings/{meeting_id}/next", json={"from_section": "scorecard"})

    with connect(sign_in, "u2") as reconnected:
        _, meeting = opened(reconnected)

    assert (meeting["meeting"]["id"], section_of(meeting)) == (meeting_id, "ids")



def test_the_end_shows_up_live(sign_in):
    meeting_id = sign_in("u2").post(START).json()["id"]
    with connect(sign_in, "u3") as live:
        opened(live)
        sign_in("u2").post(f"/api/meetings/{meeting_id}/end")
        ended = live.receive_json()

    assert ended["meeting"]["ended_at"] is not None
