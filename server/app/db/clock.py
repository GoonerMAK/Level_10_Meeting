from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.models import ClockStart


async def load_clock_start(connection: AsyncConnection, app_now: datetime) -> datetime:
    await connection.execute(
        insert(ClockStart)
        .values(app_now=app_now, started_at=datetime.now(UTC))
        .on_conflict_do_nothing(index_elements=[ClockStart.app_now])
    )
    started_at = await connection.scalar(select(ClockStart.started_at).where(ClockStart.app_now == app_now))
    await connection.commit()
    return started_at
