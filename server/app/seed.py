import asyncio
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.models import (
    Base,
    Company,
    Issue,
    Measurable,
    Meeting,
    MeetingAttendee,
    MeetingRating,
    Membership,
    Milestone,
    Rock,
    Score,
    Team,
    Todo,
    User,
)

Row = dict[str, Any]


def parse_timestamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def parse_number(value: float | int | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def measurable_row(item: Row) -> Row:
    goal = item["goal"]
    return {
        "id": item["id"],
        "team_id": item["team_id"],
        "name": item["name"],
        "owner_id": item["owner_id"],
        "unit": item["unit"],
        "goal_type": goal["type"],
        "goal_value": parse_number(goal.get("value")),
        "goal_min": parse_number(goal.get("min")),
        "goal_max": parse_number(goal.get("max")),
    }


def issue_row(item: Row) -> Row:
    source = item["source"] or {}
    return {
        "id": item["id"],
        "team_id": item["team_id"],
        "title": item["title"],
        "owner_id": item["owner_id"],
        "priority": item["priority"],
        "created_at": parse_timestamp(item["created_at"]),
        "solved_at": parse_timestamp(item["solved_at"]),
        "resolution_note": item["resolution_note"],
        "source_measurable_id": source.get("measurable_id"),
        "source_week_start": parse_date(source.get("week_start")),
    }


def todo_row(item: Row) -> Row:
    return {
        "id": item["id"],
        "team_id": item["team_id"],
        "title": item["title"],
        "owner_id": item["owner_id"],
        "due_date": parse_date(item["due_date"]),
        "done_at": parse_timestamp(item["done_at"]),
        "source_issue_id": item["source_issue_id"],
        "created_at": parse_timestamp(item["created_at"]),
    }


def meeting_row(item: Row) -> Row:
    return {
        "id": item["id"],
        "team_id": item["team_id"],
        "facilitator_id": item["facilitator_id"],
        "started_at": parse_timestamp(item["started_at"]),
        "ended_at": parse_timestamp(item["ended_at"]),
        "current_section": None,
        "section_started_at": None,
    }


def build_rows(seed: Row) -> list[tuple[type[Base], list[Row]]]:
    company = seed["company"]
    meetings = seed["meetings"]
    return [
        (Company, [{"id": company["id"], "name": company["name"], "timezone": company["timezone"]}]),
        (Team, [{**team, "company_id": company["id"]} for team in seed["teams"]]),
        (User, [{**user, "company_id": company["id"]} for user in seed["users"]]),
        (Membership, seed["memberships"]),
        (Measurable, [measurable_row(item) for item in seed["measurables"]]),
        (
            Score,
            [
                {
                    "measurable_id": item["measurable_id"],
                    "week_start": parse_date(item["week_start"]),
                    "value": parse_number(item["value"]),
                }
                for item in seed["scores"]
            ],
        ),
        (Rock, seed["rocks"]),
        (Milestone, [{**item, "due_date": parse_date(item["due_date"])} for item in seed["milestones"]]),
        (Issue, [issue_row(item) for item in seed["issues"]]),
        (Todo, [todo_row(item) for item in seed["todos"]]),
        (Meeting, [meeting_row(item) for item in meetings]),
        (
            MeetingAttendee,
            [{"meeting_id": meeting["id"], "user_id": user_id} for meeting in meetings for user_id in meeting["attendee_ids"]],
        ),
        (
            MeetingRating,
            [{"meeting_id": meeting["id"], **rating} for meeting in meetings for rating in meeting["ratings"]],
        ),
    ]


async def insert_missing(session: AsyncSession, model: type[Base], rows: list[Row]) -> None:
    if not rows:
        return
    primary_keys = [column.name for column in inspect(model).primary_key]
    statement = insert(model).values(rows).on_conflict_do_nothing(index_elements=primary_keys)
    await session.execute(statement)


async def seed_database(seed_path: Path, sessions: async_sessionmaker[AsyncSession] = SessionLocal) -> dict[str, int]:
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    async with sessions() as session, session.begin():
        for model, rows in build_rows(seed):
            await insert_missing(session, model, rows)
            counts[model.__tablename__] = len(rows)
    return counts


async def main() -> None:
    counts = await seed_database(settings.seed_path)
    await engine.dispose()
    for table, count in counts.items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
