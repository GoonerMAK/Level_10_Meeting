from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Unauthorized
from app.core.permissions import CurrentUser
from app.models import Membership, User


async def load_current_user(session: AsyncSession, user_id: str) -> CurrentUser:
    user = await session.get(User, user_id)
    if user is None:
        raise Unauthorized("Unknown user")
    team_ids = await session.scalars(select(Membership.team_id).where(Membership.user_id == user.id))
    return CurrentUser(id=user.id, name=user.name, email=user.email, role=user.role, team_ids=frozenset(team_ids))
