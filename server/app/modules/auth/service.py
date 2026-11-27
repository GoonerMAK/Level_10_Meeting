from collections.abc import MutableMapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidInput
from app.core.permissions import CurrentUser
from app.models import Membership, Team, User
from app.modules.auth.schemas import UserChoice
from app.modules.teams.schemas import TeamSummary

SIGNED_IN_USER_KEY = "user_id"


async def find_current_user(session: AsyncSession, user_id: str | None) -> CurrentUser | None:
    user = await session.get(User, user_id) if user_id else None
    if user is None:
        return None
    team_ids = await session.scalars(select(Membership.team_id).where(Membership.user_id == user.id))
    return CurrentUser(id=user.id, name=user.name, email=user.email, role=user.role, team_ids=frozenset(team_ids))


async def list_users(session: AsyncSession) -> list[UserChoice]:
    users = (await session.scalars(select(User).order_by(User.name, User.id))).all()
    memberships = await session.execute(
        select(Membership.user_id, Team.id, Team.name).join(Team, Team.id == Membership.team_id).order_by(Team.name)
    )
    teams_by_user: dict[str, list[TeamSummary]] = {}
    for user_id, team_id, team_name in memberships:
        teams_by_user.setdefault(user_id, []).append(TeamSummary(id=team_id, name=team_name))
    return [
        UserChoice(id=user.id, name=user.name, role=user.role, teams=teams_by_user.get(user.id, [])) for user in users
    ]


async def sign_in(session: AsyncSession, cookie: MutableMapping[str, Any], user_id: str) -> CurrentUser:
    current_user = await find_current_user(session, user_id)
    if current_user is None:
        raise InvalidInput("Unknown user", "user_id")
    cookie.clear()
    cookie[SIGNED_IN_USER_KEY] = current_user.id
    return current_user
