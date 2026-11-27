import asyncio
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.clock import TickingClock
from app.db.session import engine
from app.models import AppClock

SAVE_EVERY_SECONDS = 5


async def load_app_time(connection: AsyncConnection, app_now: datetime) -> datetime:
    await connection.execute(
        insert(AppClock).values(app_now=app_now, reached_at=app_now).on_conflict_do_nothing(index_elements=[AppClock.app_now])
    )
    reached_at = await connection.scalar(select(AppClock.reached_at).where(AppClock.app_now == app_now))
    await connection.commit()
    return reached_at


async def save_app_time(app_now: datetime, clock: TickingClock) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            update(AppClock)
            .where(AppClock.app_now == app_now)
            .values(reached_at=func.greatest(AppClock.reached_at, clock.now()))
        )


async def keep_saving_app_time(app_now: datetime, clock: TickingClock) -> None:
    while True:
        await asyncio.sleep(SAVE_EVERY_SECONDS)
        await save_app_time(app_now, clock)
