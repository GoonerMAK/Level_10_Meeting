from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class TeamSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class TeamMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    role: UserRole


class TodoOwner(TeamMember):
    on_team: bool


class TeamDetail(TeamSummary):
    timezone: str
    members: list[TeamMember]
    todo_owners: list[TodoOwner]
