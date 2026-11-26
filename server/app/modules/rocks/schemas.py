from datetime import date

from pydantic import BaseModel, ConfigDict

from app.core.schemas import UserRef
from app.models.enums import RockStatus


class MilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    due_date: date
    done: bool


class RockOut(BaseModel):
    id: str
    title: str
    owner: UserRef
    status: RockStatus
    progress_percent: int
    milestones: list[MilestoneOut]


class RockList(BaseModel):
    quarter: str
    rocks: list[RockOut]
