import pytest
from starlette.websockets import WebSocketDisconnect

WEB_APP = {"origin": "http://localhost:3000"}


def test_live_connection_knows_the_signed_in_user(sign_in):
    with sign_in("u2").websocket_connect("/api/live", headers=WEB_APP) as live:
        assert live.receive_json() == {"type": "hello", "user": {"id": "u2", "name": "Blake Brooks"}}


@pytest.mark.parametrize(
    ("user_id", "headers", "reason"),
    [
        (None, WEB_APP, "Choose a user first"),
        ("u2", {"origin": "https://evil.example"}, "Unknown web address"),
        ("u2", {}, "Unknown web address"),
    ],
    ids=["not signed in", "other web address", "no web address"],
)
def test_live_connection_is_refused(client, sign_in, user_id, headers, reason):
    if user_id:
        sign_in(user_id)
    with pytest.raises(WebSocketDisconnect) as refused:
        with client.websocket_connect("/api/live", headers=headers):
            pass

    assert (refused.value.code, refused.value.reason) == (1008, reason)
