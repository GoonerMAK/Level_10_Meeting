from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.error_docs import error_responses
from app.db.session import DbSession
from app.modules.auth.dependencies import SignedInUser
from app.modules.issues import service
from app.modules.issues.schemas import IssueCreate, IssueOut, IssueSolve, IssueState, PriorityUpdate
from app.modules.todos import service as todos_service
from app.modules.todos.schemas import TodoCreate, TodoOut

router = APIRouter(tags=["issues"])


@router.get("/teams/{team_id}/issues", responses=error_responses(401, 404, 422))
async def read_issues(
    team_id: str,
    session: DbSession,
    current_user: SignedInUser,
    state: Annotated[IssueState, Query(alias="status")] = "open",
) -> list[IssueOut]:
    issues = await service.list_issues(session, current_user, team_id, state)
    return [IssueOut.from_issue(issue) for issue in issues]


@router.post("/teams/{team_id}/issues", status_code=status.HTTP_201_CREATED, responses=error_responses(401, 403, 404, 422))
async def create_issue(team_id: str, body: IssueCreate, session: DbSession, current_user: SignedInUser) -> IssueOut:
    issue = await service.create_issue(session, current_user, team_id, body.title, body.priority)
    return IssueOut.from_issue(issue)


@router.patch("/issues/{issue_id}", responses=error_responses(401, 403, 404, 409, 422))
async def update_priority(issue_id: str, body: PriorityUpdate, session: DbSession, current_user: SignedInUser) -> IssueOut:
    issue = await service.set_priority(session, current_user, issue_id, body.priority)
    return IssueOut.from_issue(issue)


@router.post("/issues/{issue_id}/solve", responses=error_responses(401, 403, 404, 409, 422))
async def solve_issue(issue_id: str, body: IssueSolve, session: DbSession, current_user: SignedInUser) -> IssueOut:
    issue = await service.solve_issue(session, current_user, issue_id, body.resolution_note)
    return IssueOut.from_issue(issue)


@router.post("/issues/{issue_id}/todos", status_code=status.HTTP_201_CREATED, responses=error_responses(401, 403, 404, 422))
async def add_todo(issue_id: str, body: TodoCreate, session: DbSession, current_user: SignedInUser) -> TodoOut:
    return await todos_service.add_todo_to_issue(session, current_user, issue_id, body.title, body.owner_id)
