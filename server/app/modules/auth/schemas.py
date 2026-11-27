from pydantic import BaseModel

from app.core.permissions import CurrentUser
from app.models.enums import UserRole
from app.modules.teams.schemas import TeamSummary


class Me(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    team_ids: list[str]

    @classmethod
    def from_user(cls, current_user: CurrentUser) -> "Me":
        return cls(
            id=current_user.id,
            name=current_user.name,
            email=current_user.email,
            role=current_user.role,
            team_ids=sorted(current_user.team_ids),
        )


class UserChoice(BaseModel):
    id: str
    name: str
    role: UserRole
    teams: list[TeamSummary]


class SignIn(BaseModel):
    user_id: str
