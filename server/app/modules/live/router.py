from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.schemas import UserRef
from app.modules.auth.dependencies import LiveUser

router = APIRouter(tags=["live"])


@router.websocket("/live")
async def live(websocket: WebSocket, current_user: LiveUser) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "hello", "user": UserRef(id=current_user.id, name=current_user.name).model_dump()})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
