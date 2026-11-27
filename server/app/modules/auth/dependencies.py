from typing import Annotated

from fastapi import Depends, Request, WebSocket, WebSocketException, status

from app.core.config import settings
from app.core.errors import Unauthorized
from app.core.permissions import CurrentUser
from app.db.session import DbSession, SessionLocal
from app.modules.auth.service import find_current_user, signed_in_user_id


async def get_current_user(request: Request, session: DbSession) -> CurrentUser:
    current_user = await find_current_user(session, signed_in_user_id(request.session))
    if current_user is None:
        request.session.clear()
        raise Unauthorized("Choose a user first")
    return current_user


async def get_live_user(websocket: WebSocket) -> CurrentUser:
    if websocket.headers.get("origin") != settings.web_origin:
        raise WebSocketException(status.WS_1008_POLICY_VIOLATION, "Unknown web address")
    async with SessionLocal() as session:
        current_user = await find_current_user(session, signed_in_user_id(websocket.session))
    if current_user is None:
        raise WebSocketException(status.WS_1008_POLICY_VIOLATION, "Choose a user first")
    return current_user


SignedInUser = Annotated[CurrentUser, Depends(get_current_user)]
LiveUser = Annotated[CurrentUser, Depends(get_live_user)]
