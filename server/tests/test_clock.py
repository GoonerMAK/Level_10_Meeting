import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core import clock
from app.core.clock import TickingClock, use_clock, utc_now
from app.core.config import Settings, settings
from app.db.clock import load_app_time, save_app_time
from app.db.session import SessionLocal, engine
from app.main import app
from app.models import AppClock


def run_and_dispose(work):
    async def run():
        try:
            return await work()
        finally:
            await engine.dispose()

    return asyncio.run(run())


async def store_app_time(app_now, reached_at):
    async with SessionLocal() as session:
        await session.execute(
            insert(AppClock)
            .values(app_now=app_now, reached_at=reached_at)
            .on_conflict_do_update(index_elements=[AppClock.app_now], set_={"reached_at": reached_at})
        )
        await session.commit()


async def stored_app_times(*app_nows):
    async with SessionLocal() as session:
        rows = await session.execute(select(AppClock.app_now, AppClock.reached_at).where(AppClock.app_now.in_(app_nows)))
        return dict(rows.all())


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
    use_clock(TickingClock(settings.app_now + timedelta(days=7)))

    response = sign_in("u2").get("/api/teams/team_lead/scorecard")

    assert response.status_code == 200
    assert utc_now() - settings.app_now >= timedelta(days=7)
    assert response.json()["current_week"] == "2026-11-09"


def test_a_fresh_clock_starts_at_app_now():
    fresh = TickingClock(settings.app_now)

    assert timedelta(0) <= fresh.now() - settings.app_now < timedelta(seconds=1)


def test_the_clock_counts_run_time_only(monkeypatch):
    run_seconds = iter([100.0, 130.0])
    monkeypatch.setattr(clock, "monotonic", lambda: next(run_seconds))

    ticking = TickingClock(settings.app_now)

    assert ticking.now() == settings.app_now + timedelta(seconds=30)


def test_the_stored_time_is_kept_and_a_new_app_now_gets_its_own(migrated_database):
    later_app_now = settings.app_now + timedelta(days=30)

    async def load():
        async with engine.connect() as connection:
            first = await load_app_time(connection, settings.app_now)
            again = await load_app_time(connection, settings.app_now)
            later = await load_app_time(connection, later_app_now)
        return first, again, later, await stored_app_times(settings.app_now, later_app_now)

    first, again, later, stored = run_and_dispose(load)

    assert first == again
    assert later == later_app_now
    assert set(stored) == {settings.app_now, later_app_now}


def test_a_saved_time_never_moves_back(migrated_database):
    app_now = settings.app_now + timedelta(days=60)
    reached = app_now + timedelta(hours=2)

    async def save_earlier():
        await store_app_time(app_now, reached)
        await save_app_time(app_now, TickingClock(app_now))
        return await stored_app_times(app_now)

    assert run_and_dispose(save_earlier)[app_now] == reached


def test_a_restarted_server_resumes_where_it_stopped(seeded_database):
    stopped_at = settings.app_now + timedelta(hours=1)
    run_and_dispose(lambda: store_app_time(settings.app_now, stopped_at))

    with TestClient(app):
        resumed = utc_now()

    saved = run_and_dispose(lambda: stored_app_times(settings.app_now))[settings.app_now]
    assert timedelta(0) <= resumed - stopped_at < timedelta(minutes=1)
    assert saved >= resumed
