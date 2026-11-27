from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

from app.core.schemas import UserRef
from app.modules.meetings.schemas import MeetingState

TeamData = Literal["scorecard", "issues", "todos"]


class Hello(BaseModel):
    type: Literal["hello"] = "hello"
    user: UserRef


class MeetingMessage(BaseModel):
    type: Literal["meeting"] = "meeting"
    meeting: MeetingState | None


class Changed(BaseModel):
    type: Literal["changed"] = "changed"
    what: TeamData


LiveMessage = Annotated[Hello | MeetingMessage | Changed, Field(discriminator="type")]
live_message = TypeAdapter(LiveMessage)
