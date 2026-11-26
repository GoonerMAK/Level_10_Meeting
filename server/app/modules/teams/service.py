from collections.abc import Sequence
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculations.time import CompanyClock
from app.core.clock import calendar_now
from app.core.errors import NotFound
from app.core.permissions import CurrentUser, ensure_can_change_team, ensure_can_read_team
from app.models import Company, Issue, Measurable, Membership, Team, Todo, User
from app.models.enums import UserRole


async def list_teams(session: AsyncSession, current_user: CurrentUser) -> Sequence[Team]:
    query = select(Team).order_by(Team.name)
    if current_user.role is not UserRole.ADMIN:
        query = query.where(Team.id.in_(current_user.team_ids))
    return (await session.scalars(query)).all()


async def get_readable_team(session: AsyncSession, current_user: CurrentUser, team_id: str) -> Team:
    ensure_can_read_team(current_user, team_id)
    team = await session.get(Team, team_id)
    if team is None:
        raise NotFound("Team not found")
    return team


async def get_changeable_team(session: AsyncSession, current_user: CurrentUser, team_id: str) -> Team:
    team = await get_readable_team(session, current_user, team_id)
    ensure_can_change_team(current_user, team_id)
    return team


async def get_team_with_members(
    session: AsyncSession, current_user: CurrentUser, team_id: str
) -> tuple[Team, Sequence[User]]:
    team = await get_readable_team(session, current_user, team_id)
    members = await session.scalars(
        select(User).join(Membership, Membership.user_id == User.id).where(Membership.team_id == team_id).order_by(User.name)
    )
    return team, members.all()


async def company_clock(session: AsyncSession, team_id: str) -> CompanyClock:
    timezone = await session.scalar(
        select(Company.timezone).join(Team, Team.company_id == Company.id).where(Team.id == team_id)
    )
    if timezone is None:
        raise NotFound("Team not found")
    return CompanyClock(now=calendar_now(), timezone=ZoneInfo(timezone))


async def readable_team_clock(session: AsyncSession, current_user: CurrentUser, team_id: str) -> CompanyClock:
    ensure_can_read_team(current_user, team_id)
    return await company_clock(session, team_id)


async def get_changeable_row[Row: Issue | Measurable | Todo](
    session: AsyncSession, current_user: CurrentUser, model: type[Row], row_id: str, resource: str
) -> Row:
    row = await session.get(model, row_id)
    if row is None:
        raise NotFound(f"{resource} not found")
    ensure_can_change_team(current_user, row.team_id, resource)
    return row
