from fastapi import APIRouter

from app.core.error_docs import error_responses
from app.db.session import DbSession
from app.modules.auth.dependencies import SignedInUser
from app.modules.todos import service
from app.modules.todos.schemas import TodoList, TodoOut

router = APIRouter(tags=["todos"])


@router.get("/teams/{team_id}/todos", responses=error_responses(401, 404))
async def read_todos(team_id: str, session: DbSession, current_user: SignedInUser) -> TodoList:
    return await service.list_todos(session, current_user, team_id)


@router.post("/todos/{todo_id}/done", responses=error_responses(401, 403, 404))
async def mark_done(todo_id: str, session: DbSession, current_user: SignedInUser) -> TodoOut:
    return await service.set_todo_done(session, current_user, todo_id, done=True)


@router.post("/todos/{todo_id}/undo", responses=error_responses(401, 403, 404))
async def mark_not_done(todo_id: str, session: DbSession, current_user: SignedInUser) -> TodoOut:
    return await service.set_todo_done(session, current_user, todo_id, done=False)
