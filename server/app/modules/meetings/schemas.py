from datetime import datetime

from pydantic import BaseModel

from app.core.schemas import UserRef
from app.models.enums import MeetingSection


class MeetingState(BaseModel):
    id: str
    team_id: str
    facilitator: UserRef
    attendees: list[UserRef]
    started_at: datetime
    ended_at: datetime | None
    section: MeetingSection | None
    section_started_at: datetime | None
    section_ends_at: datetime | None
    over_time: bool
    server_now: datetime


class NextSection(BaseModel):
    from_section: MeetingSection

