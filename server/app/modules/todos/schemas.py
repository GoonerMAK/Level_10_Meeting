from datetime import date, datetime

from pydantic import BaseModel

from app.calculations.time import CompanyClock
from app.calculations.todos import Completion, is_overdue
from app.core.schemas import Title, UserRef
from app.models import Todo


class TodoSourceIssue(BaseModel):
    id: str
    title: str


class TodoOut(BaseModel):
    id: str
    title: str
    owner: UserRef
    due_date: date
    done_at: datetime | None
    overdue: bool
    source_issue: TodoSourceIssue | None

    @classmethod
    def from_todo(cls, todo: Todo, clock: CompanyClock) -> "TodoOut":
        source = todo.source_issue
        return cls(
            id=todo.id,
            title=todo.title,
            owner=UserRef.model_validate(todo.owner),
            due_date=todo.due_date,
            done_at=todo.done_at,
            overdue=is_overdue(todo, clock.today),
            source_issue=TodoSourceIssue(id=source.id, title=source.title) if source is not None else None,
        )


class TodoList(BaseModel):
    completion_week: date
    completion: Completion | None
    todos: list[TodoOut]


class TodoCreate(BaseModel):
    title: Title
    owner_id: str
