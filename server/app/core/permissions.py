from dataclasses import dataclass

from app.core.errors import Forbidden, NotFound
from app.models.enums import UserRole


@dataclass(frozen=True)
class CurrentUser:
    id: str
    name: str
    email: str
    role: UserRole
    team_ids: frozenset[str]


def ensure_can_read_team(current_user: CurrentUser, team_id: str) -> None:
    if current_user.role is not UserRole.ADMIN and team_id not in current_user.team_ids:
        raise NotFound("Team not found")


def ensure_can_change_team(current_user: CurrentUser, team_id: str) -> None:
    ensure_can_read_team(current_user, team_id)
    if current_user.role is UserRole.OBSERVER:
        raise Forbidden("Observers can view this team but cannot change anything")
