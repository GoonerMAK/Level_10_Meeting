import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

import asyncpg
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.calculations.issues import in_issue_order
from app.calculations.rocks import rock_progress, rock_status
from app.calculations.scorecard import score_status
from app.calculations.time import CompanyClock
from app.calculations.todos import completion_for_week, is_overdue
from app.core.config import SERVER_ROOT, settings
from app.models import Issue, Measurable, Meeting, Rock, Score, Team, Todo
from app.modules.meetings.service import meeting_summary
from app.modules.teams.service import company_timezone
from app.seed import seed_database

Report = dict[str, Any]


def utc_text(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


async def build_report(session: AsyncSession, now: datetime) -> Report:
    team_ids = (await session.scalars(select(Team.id).order_by(Team.id))).all()
    return {"now": utc_text(now), "teams": {team_id: await team_report(session, team_id, now) for team_id in team_ids}}


async def team_report(session: AsyncSession, team_id: str, now: datetime) -> Report:
    clock = CompanyClock(now=now, timezone=await company_timezone(session, team_id))
    todos = (await session.scalars(select(Todo).where(Todo.team_id == team_id))).all()
    return {
        "measurable_status": await measurable_statuses(session, team_id, clock),
        "todo_completion": {
            week.isoformat(): completion and asdict(completion)
            for week in clock.scorecard_weeks
            for completion in [completion_for_week(todos, week, clock)]
        },
        "overdue_todos": sorted(todo.id for todo in todos if is_overdue(todo, clock.today)),
        "rocks": await rock_statuses(session, team_id, clock),
        "issue_order": await unsolved_issue_order(session, team_id),
        "meetings": await meeting_summaries(session, team_id),
    }


async def measurable_statuses(session: AsyncSession, team_id: str, clock: CompanyClock) -> Report:
    weeks = clock.scorecard_weeks
    measurables = (await session.scalars(select(Measurable).where(Measurable.team_id == team_id).order_by(Measurable.id))).all()
    scores = await session.execute(
        select(Score.measurable_id, Score.week_start, Score.value).where(
            Score.measurable_id.in_([measurable.id for measurable in measurables]),
            Score.week_start.between(weeks[0], weeks[-1]),
        )
    )
    values = {(measurable_id, week): value for measurable_id, week, value in scores}
    return {
        measurable.id: {
            week.isoformat(): score_status(measurable, values.get((measurable.id, week)), week, clock.current_week)
            for week in weeks
        }
        for measurable in measurables
    }


async def rock_statuses(session: AsyncSession, team_id: str, clock: CompanyClock) -> Report:
    rocks = await session.scalars(
        select(Rock).where(Rock.team_id == team_id).options(selectinload(Rock.milestones)).order_by(Rock.id)
    )
    return {
        rock.id: {
            "status": rock_status(rock.status, rock.milestones, clock.today),
            "progress_percent": rock_progress(rock.status, rock.milestones),
        }
        for rock in rocks
    }


async def unsolved_issue_order(session: AsyncSession, team_id: str) -> list[str]:
    issues = await session.scalars(select(Issue).where(Issue.team_id == team_id, Issue.solved_at.is_(None)))
    return [issue.id for issue in in_issue_order(issues)]


async def meeting_summaries(session: AsyncSession, team_id: str) -> Report:
    meetings = await session.scalars(
        select(Meeting).where(Meeting.team_id == team_id, Meeting.ended_at.is_not(None)).order_by(Meeting.id)
    )
    report: Report = {}
    for meeting in meetings.all():
        assert meeting.ended_at is not None
        summary = await meeting_summary(session, meeting, meeting.ended_at)
        report[meeting.id] = {
            "scorecard_week": summary.scorecard_week.isoformat(),
            "measurable_status": {row.id: row.status for row in summary.measurables},
            "issues_solved": sorted(issue.id for issue in summary.issues_solved),
            "todos_created": sorted(todo.id for todo in summary.todos_created),
            "attendee_ids": sorted(attendee.id for attendee in summary.attendees),
            "rating": float(summary.rating) if summary.rating is not None else None,
        }
    return report


def report_database_url() -> URL:
    url = make_url(settings.database_url)
    return url.set(database=f"{url.database}_report")


async def run_admin_sql(url: URL, statement: str) -> None:
    admin_url = url.set(drivername="postgresql", database="postgres")
    connection = await asyncpg.connect(admin_url.render_as_string(hide_password=False))
    try:
        await connection.execute(statement)
    finally:
        await connection.close()


def migrate(url: URL) -> None:
    config = Config(str(SERVER_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False).replace("%", "%%"))
    command.upgrade(config, "head")


@asynccontextmanager
async def freshly_seeded(url: URL) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    drop = f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'
    await run_admin_sql(url, drop)
    await run_admin_sql(url, f'CREATE DATABASE "{url.database}"')
    engine = create_async_engine(url)
    try:
        await asyncio.to_thread(migrate, url)
        sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        await seed_database(settings.seed_path, sessions)
        yield sessions
    finally:
        await engine.dispose()
        await run_admin_sql(url, drop)


async def fresh_report(now: datetime) -> Report:
    async with freshly_seeded(report_database_url()) as sessions, sessions() as session:
        return await build_report(session, now)


def main() -> None:
    print(json.dumps(asyncio.run(fresh_report(settings.app_now)), indent=2))


if __name__ == "__main__":
    main()
