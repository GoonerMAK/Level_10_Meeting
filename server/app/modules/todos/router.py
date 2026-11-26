from fastapi import APIRouter

from app.db.session import DbSession
from app.modules.auth.dependencies import SignedInUser
from app.modules.todos import service
from app.modules.todos.schemas import TodoList, TodoOut

router = APIRouter(tags=["todos"])


@router.get("/teams/{team_id}/todos")
async def read_todos(team_id: str, session: DbSession, current_user: SignedInUser) -> TodoList:
    return await service.list_todos(session, current_user, team_id)


@router.post("/todos/{todo_id}/done")
async def mark_done(todo_id: str, session: DbSession, current_user: SignedInUser) -> TodoOut:
    return await service.set_todo_done(session, current_user, todo_id, done=True)


@router.post("/todos/{todo_id}/undo")
async def mark_not_done(todo_id: str, session: DbSession, current_user: SignedInUser) -> TodoOut:
    return await service.set_todo_done(session, current_user, todo_id, done=False)
