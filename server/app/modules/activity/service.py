from collections.abc import Iterable
from typing import Any

from pydantic_core import to_jsonable_python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import CurrentUser
from app.models import ActivityLog, User
from app.models.enums import AuditAction, AuditEntity
from app.modules.activity.schemas import ActivityOut, Change
from app.modules.teams.service import get_readable_team

Changed = tuple[str, Any, Any]


def record(
    session: AsyncSession,
    *,
    user_id: str | None,
    team_id: str,
    entity: AuditEntity,
    entity_id: str,
    label: str,
    action: AuditAction,
    changes: Iterable[Changed] = (),
) -> None:
    session.add(
        ActivityLog(
            user_id=user_id,
            team_id=team_id,
            entity=entity,
            entity_id=entity_id,
            entity_label=label,
            action=action,
            changes=[
                {"field": field, "before": to_jsonable_python(before), "after": to_jsonable_python(after)}
                for field, before, after in changes
            ],
        )
    )


async def list_activity(
    session: AsyncSession, current_user: CurrentUser, team_id: str, limit: int, before_id: int | None
) -> list[ActivityOut]:
    await get_readable_team(session, current_user, team_id)
    query = (
        select(ActivityLog, User)
        .outerjoin(User, User.id == ActivityLog.user_id)
        .where(ActivityLog.team_id == team_id)
        .order_by(ActivityLog.id.desc())
        .limit(limit)
    )
    if before_id is not None:
        query = query.where(ActivityLog.id < before_id)
    rows = await session.execute(query)
    return [
        ActivityOut(
            id=entry.id,
            created_at=entry.created_at,
            user={"id": user.id, "name": user.name} if user else None,
            entity=entry.entity,
            entity_id=entry.entity_id,
            entity_label=entry.entity_label,
            action=entry.action,
            changes=[Change.model_validate(change) for change in entry.changes],
        )
        for entry, user in rows
    ]
