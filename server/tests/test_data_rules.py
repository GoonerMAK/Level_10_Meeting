import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core import errors
from app.core.errors import register_error_handlers
from app.core.messages import DATA_RULES
from app.db.session import SessionLocal, engine

NAMED_RULES_SQL = """
SELECT conname AS name FROM pg_constraint
WHERE contype IN ('c', 'u') AND connamespace = 'public'::regnamespace
UNION
SELECT indexname AS name FROM pg_indexes
WHERE schemaname = 'public' AND indexdef LIKE 'CREATE UNIQUE%' AND indexname NOT LIKE 'pk_%'
"""


async def named_database_rules() -> set[str]:
    async with SessionLocal() as session:
        names = set(await session.scalars(text(NAMED_RULES_SQL)))
    await engine.dispose()
    return names - {"alembic_version_pkc"}


def test_every_check_and_unique_rule_has_a_plain_message(migrated_database):
    assert asyncio.run(named_database_rules()) - DATA_RULES.keys() == set()


def run_on_database(statement):
    app = FastAPI()
    register_error_handlers(app)

    @app.post("/change")
    async def change() -> None:
        async with SessionLocal() as session:
            await session.execute(text(statement))
            await session.commit()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/change")
    asyncio.run(engine.dispose())
    return response


def field_error(message, field):
    return {"code": "invalid_input", "message": message, "fields": [{"field": field, "message": message}]}


BROKEN_RULES = [
    pytest.param(
        "UPDATE issues SET priority = 6 WHERE id = 'i8'",
        422,
        field_error("Priority must be 1 to 5", "priority"),
        id="priority_range",
    ),
    pytest.param(
        "UPDATE issues SET solved_at = now() WHERE id = 'i8'",
        422,
        field_error("A solved Issue needs a note, and an open one has none", "resolution_note"),
        id="solved_requires_note",
    ),
    pytest.param(
        "UPDATE meetings SET ended_at = NULL, current_section = 'scorecard', section_started_at = now() WHERE id IN ('mt1', 'mt2')",
        409,
        {"code": "conflict", "message": "This team already has a meeting running"},
        id="one_active_meeting_per_team",
    ),
    pytest.param(
        "UPDATE todos SET owner_id = 'nobody' WHERE id = 't41'",
        422,
        field_error("Owner must be a Team Member of this team or an Admin", "owner_id"),
        id="todo_owner_exists",
    ),
    pytest.param(
        "UPDATE todos SET title = NULL WHERE id = 't41'",
        422,
        field_error("Title is required, up to 200 characters", "title"),
        id="required_value",
    ),
    pytest.param(
        "UPDATE memberships SET team_id = 'team_nowhere' WHERE user_id = 'u9'",
        422,
        {"code": "invalid_input", "message": "Something this change points to doesn't exist"},
        id="unmapped_link",
    ),
]


@pytest.mark.parametrize(("statement", "status", "error"), BROKEN_RULES)
def test_a_broken_database_rule_gets_a_plain_message(seeded_database, statement, status, error):
    response = run_on_database(statement)

    assert response.status_code == status
    assert response.json() == {"error": error}


def test_an_unmapped_database_rule_is_a_generic_conflict(seeded_database, monkeypatch):
    monkeypatch.delitem(errors.DATA_RULES, "ck_issues_priority_range")

    response = run_on_database("UPDATE issues SET priority = 6 WHERE id = 'i8'")

    assert response.status_code == 409
    assert response.json() == {"error": {"code": "conflict", "message": "This change breaks a data rule"}}
