import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.core.clock import TickingClock, use_clock, utc_now
from app.core.config import Settings, settings
from app.db.clock import load_clock_start
from app.db.session import SessionLocal, engine
from app.main import app
from app.models import ClockStart


def load_starts(*app_nows):
    async def load():
        starts = []
        for app_now in app_nows:
            async with engine.connect() as connection:
                starts.append(await load_clock_start(connection, app_now))
        async with SessionLocal() as session:
            rows = await session.scalar(select(func.count()).select_from(ClockStart))
        await engine.dispose()
        return starts, rows

    return asyncio.run(load())


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-11-18T15:00:00", datetime(2026, 11, 18, 15, 0, tzinfo=UTC)),
        ("2026-11-18T15:00:00Z", datetime(2026, 11, 18, 15, 0, tzinfo=UTC)),
        ("2026-11-18T09:00:00-06:00", datetime(2026, 11, 18, 15, 0, tzinfo=UTC)),
    ],
    ids=["no time zone", "utc", "chicago offset"],
)
def test_app_now_is_read_as_utc(value, expected):
    app_now = Settings(app_now=value).app_now

    assert app_now == expected
    assert app_now.utcoffset() == timedelta(0)


def test_today_stays_on_the_app_now_date_while_the_clock_ticks(sign_in):
    use_clock(TickingClock(settings.app_now, datetime.now(UTC) - timedelta(days=7)))

    response = sign_in("u2").get("/api/teams/team_lead/scorecard")

    assert utc_now() - settings.app_now > timedelta(days=7)
    assert response.json()["current_week"] == "2026-11-09"


def test_a_fresh_clock_starts_at_app_now():
    clock = TickingClock(settings.app_now, datetime.now(UTC))

    assert timedelta(0) <= clock.now() - settings.app_now < timedelta(seconds=1)


def test_the_stored_start_is_kept_and_a_new_app_now_gets_its_own(migrated_database):
    later_app_now = settings.app_now + timedelta(days=30)

    (first, again, later), rows = load_starts(settings.app_now, settings.app_now, later_app_now)

    assert first == again
    assert later >= first
    assert rows == 2


def test_a_restarted_server_resumes_the_stored_clock(seeded_database):
    asyncio.run(store_clock_start(settings.app_now, datetime.now(UTC) - timedelta(hours=1)))
    use_clock(TickingClock(settings.app_now, datetime.now(UTC)))

    with TestClient(app):
        resumed = utc_now()

    assert resumed - settings.app_now >= timedelta(hours=1)


async def store_clock_start(app_now, started_at):
    async with SessionLocal() as session:
        await session.execute(
            insert(ClockStart)
            .values(app_now=app_now, started_at=started_at)
            .on_conflict_do_update(index_elements=[ClockStart.app_now], set_={"started_at": started_at})
        )
        await session.commit()
    await engine.dispose()
