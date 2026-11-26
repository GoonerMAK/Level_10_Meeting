from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.core.schemas import Note, Title, UserRef
from app.models import Issue

Priority = Annotated[int, Field(ge=1, le=5)]
IssueState = Literal["open", "solved"]


class IssueSource(BaseModel):
    measurable_id: str
    measurable_name: str
    week_start: date


class IssueOut(BaseModel):
    id: str
    title: str
    owner: UserRef
    priority: int | None
    created_at: datetime
    solved_at: datetime | None
    resolution_note: str | None
    source: IssueSource | None

    @classmethod
    def from_issue(cls, issue: Issue) -> "IssueOut":
        source = None
        if issue.source_measurable is not None and issue.source_week_start is not None:
            source = IssueSource(
                measurable_id=issue.source_measurable.id,
                measurable_name=issue.source_measurable.name,
                week_start=issue.source_week_start,
            )
        return cls(
            id=issue.id,
            title=issue.title,
            owner=UserRef.model_validate(issue.owner),
            priority=issue.priority,
            created_at=issue.created_at,
            solved_at=issue.solved_at,
            resolution_note=issue.resolution_note,
            source=source,
        )


class IssueCreate(BaseModel):
    title: Title
    priority: Priority | None = None


class PriorityUpdate(BaseModel):
    priority: Priority | None


class IssueSolve(BaseModel):
    resolution_note: Note
