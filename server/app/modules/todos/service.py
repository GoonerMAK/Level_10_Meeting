from datetime import timedelta
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.calculations.time import CompanyClock
from app.calculations.todos import completion_for_week
from app.core.clock import utc_now
from app.core.errors import InvalidInput, NotFound
from app.core.permissions import CurrentUser
from app.models import Issue, Todo, User
from app.models.enums import AuditAction, AuditEntity
from app.modules.activity.service import Changed, record
from app.modules.live.hub import publish_change
from app.modules.teams.service import can_own_todos, company_clock, get_changeable_row, readable_team_clock
from app.modules.todos.schemas import TodoList, TodoOut

TODO_DETAILS = (selectinload(Todo.owner), selectinload(Todo.source_issue))
DUE_AFTER = timedelta(days=7)


async def todo_out(session: AsyncSession, todo_id: str, clock: CompanyClock) -> TodoOut:
    todo = await session.scalar(select(Todo).where(Todo.id == todo_id).options(*TODO_DETAILS))
    if todo is None:
        raise NotFound("To-Do not found")
    return TodoOut.from_todo(todo, clock)


async def list_todos(session: AsyncSession, current_user: CurrentUser, team_id: str) -> TodoList:
    clock = await readable_team_clock(session, current_user, team_id)
    week = clock.last_closed_week
    shown = (
        await session.scalars(
            select(Todo)
            .where(Todo.team_id == team_id, or_(Todo.done_at.is_(None), Todo.done_at >= clock.start_of_day(week)))
            .options(*TODO_DETAILS)
            .order_by(Todo.due_date, Todo.id)
        )
    ).all()
    due_that_week = await session.scalars(
        select(Todo).where(Todo.team_id == team_id, Todo.due_date.between(week, week + timedelta(days=6)))
    )
    return TodoList(
        completion_week=week,
        completion=completion_for_week(due_that_week, week, clock),
        todos=[TodoOut.from_todo(todo, clock) for todo in shown],
    )


async def ensure_can_own_todos(session: AsyncSession, team_id: str, owner_id: str) -> None:
    owner = await session.scalar(select(User.id).where(User.id == owner_id, can_own_todos(team_id)))
    if owner is None:
        raise InvalidInput("Owner must be a Team Member of this team or an Admin", "owner_id")


def record_todo(
    session: AsyncSession, current_user: CurrentUser, todo: Todo, action: AuditAction, changes: list[Changed]
) -> None:
    record(
        session,
        user_id=current_user.id,
        team_id=todo.team_id,
        entity=AuditEntity.TODO,
        entity_id=todo.id,
        label=todo.title,
        action=action,
        changes=changes,
    )


async def add_todo_to_issue(
    session: AsyncSession, current_user: CurrentUser, issue_id: str, title: str, owner_id: str
) -> TodoOut:
    issue = await get_changeable_row(session, current_user, Issue, issue_id, "Issue")
    await ensure_can_own_todos(session, issue.team_id, owner_id)
    clock = await company_clock(session, issue.team_id)
    todo = Todo(
        id=str(uuid4()),
        team_id=issue.team_id,
        title=title,
        owner_id=owner_id,
        due_date=clock.today + DUE_AFTER,
        source_issue_id=issue.id,
    )
    session.add(todo)
    record_todo(
        session,
        current_user,
        todo,
        AuditAction.CREATED,
        [("owner_id", None, owner_id), ("due_date", None, todo.due_date), ("source_issue_id", None, issue.id)],
    )
    await session.commit()
    await publish_change(issue.team_id, "todos")
    return await todo_out(session, todo.id, clock)


async def set_todo_done(session: AsyncSession, current_user: CurrentUser, todo_id: str, done: bool) -> TodoOut:
    todo = await get_changeable_row(session, current_user, Todo, todo_id, "To-Do")
    previous = todo.done_at
    if done and todo.done_at is None:
        todo.done_at = utc_now()
    if not done:
        todo.done_at = None
    if todo.done_at != previous:
        record_todo(session, current_user, todo, AuditAction.UPDATED, [("done_at", previous, todo.done_at)])
    await session.commit()
    await publish_change(todo.team_id, "todos")
    return await todo_out(session, todo_id, await company_clock(session, todo.team_id))
