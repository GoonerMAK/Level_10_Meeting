from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, status

from app.core.permissions import CurrentUser, can_read_team
from app.core.schemas import UserRef
from app.db.session import SessionLocal
from app.models import Team
from app.modules.auth.dependencies import LiveUser
from app.modules.live.hub import current_hub
from app.modules.meetings.service import active_meeting_state, meeting_message

router = APIRouter(tags=["live"])


@router.websocket("/live")
async def live(websocket: WebSocket, current_user: LiveUser, team_id: str) -> None:
    await ensure_readable_team(current_user, team_id)
    hub = current_hub()
    await websocket.accept()
    await websocket.send_json({"type": "hello", "user": UserRef(id=current_user.id, name=current_user.name).model_dump()})
    async with hub.in_order(team_id):
        async with SessionLocal() as session:
            state = await active_meeting_state(session, team_id)
        await websocket.send_json(meeting_message(state))
        hub.add(team_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
    finally:
        hub.remove(team_id, websocket)


async def ensure_readable_team(current_user: CurrentUser, team_id: str) -> None:
    async with SessionLocal() as session:
        team = await session.get(Team, team_id)
    if team is None or not can_read_team(current_user, team_id):
        raise WebSocketException(status.WS_1008_POLICY_VIOLATION, "Team not found")
