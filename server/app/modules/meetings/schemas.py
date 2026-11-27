from datetime import datetime

from typing import Annotated

from pydantic import BaseModel, Field

from app.core.schemas import UserRef
from app.models.enums import MeetingSection


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


class NextSection(BaseModel):
    from_section: MeetingSection


class RatingUpdate(BaseModel):
    rating: Annotated[int, Field(ge=1, le=10)]
