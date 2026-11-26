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


def can_read_team(current_user: CurrentUser, team_id: str) -> bool:
    return current_user.role is UserRole.ADMIN or team_id in current_user.team_ids


def ensure_can_read_team(current_user: CurrentUser, team_id: str, resource: str = "Team") -> None:
    if not can_read_team(current_user, team_id):
        raise NotFound(f"{resource} not found")


def ensure_can_change_team(current_user: CurrentUser, team_id: str, resource: str = "Team") -> None:
    ensure_can_read_team(current_user, team_id, resource)
    if current_user.role is UserRole.OBSERVER:
        raise Forbidden("Observers can view this team but cannot change anything")
