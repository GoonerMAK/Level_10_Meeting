from datetime import date, datetime

from typing import Annotated

from pydantic import BaseModel, Field

from app.calculations.scorecard import ScoreStatus
from app.core.schemas import JsonNumber, UserRef
from app.models.enums import MeetingSection
from app.modules.scorecard.schemas import Goal


class MeetingRatingOut(BaseModel):
    user: UserRef
    rating: int


class MeetingState(BaseModel):
    id: str
    team_id: str
    facilitator: UserRef
    attendees: list[UserRef]
    ratings: list[MeetingRatingOut]
    started_at: datetime
    ended_at: datetime | None
    section: MeetingSection | None
    section_started_at: datetime | None
    section_ends_at: datetime | None
    over_time: bool
    server_now: datetime


class SummaryMeasurable(BaseModel):
    id: str
    name: str
    owner: UserRef
    unit: str
    goal: Goal
    value: JsonNumber | None
    status: ScoreStatus


class SummaryIssue(BaseModel):
    id: str
    title: str
    owner: UserRef
    solved_at: datetime


class SummaryTodo(BaseModel):
    id: str
    title: str
    owner: UserRef
    due_date: date
    created_at: datetime


class MeetingSummary(BaseModel):
    id: str
    team_id: str
    started_at: datetime
    ended_at: datetime
    scorecard_week: date
    measurables: list[SummaryMeasurable]
    issues_solved: list[SummaryIssue]
    todos_created: list[SummaryTodo]
    attendees: list[UserRef]
    ratings: list[MeetingRatingOut]
    rating: JsonNumber | None


class NextSection(BaseModel):
    from_section: MeetingSection


class RatingUpdate(BaseModel):
    rating: Annotated[int, Field(ge=1, le=10)]
