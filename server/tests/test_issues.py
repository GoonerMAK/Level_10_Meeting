import asyncio
from datetime import date

import pytest
from sqlalchemy import delete, func, select, update

from app.core.clock import utc_now
from app.db.session import SessionLocal, engine
from app.models import Issue
from app.modules.issues import service


def test_observer_write_is_refused(sign_in):
    response = sign_in("u5").post("/api/teams/team_lead/issues", json={"title": "Hiring plan"})

    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "forbidden", "message": "Observers can view this team but cannot change anything"}
    }


@pytest.mark.anyio
async def test_clicks_at_once_make_one_issue(signed_in_clients):
    url = "/api/measurables/m3/scores/2026-11-02/issue"
    users = [f"u{click % 4 + 1}" for click in range(10)]
    async with signed_in_clients(*sorted(set(users))) as clients:
        responses = await asyncio.gather(*(clients[user].post(url) for user in users))
    try:
        assert sorted(response.status_code for response in responses) == [200] * 9 + [201]
        assert len({response.json()["id"] for response in responses}) == 1
        assert await count_open_score_issues("m3", date(2026, 11, 2)) == 1
    finally:
        await delete_score_issues("m3", date(2026, 11, 2))
        await engine.dispose()


@pytest.mark.anyio
async def test_issue_solved_mid_click_gives_a_fresh_issue(signed_in_clients, monkeypatch):
    url = "/api/measurables/m5/scores/2026-11-02/issue"
    find_open_issue_id = service.find_open_score_issue_id

    async def solve_before_find(session, measurable_id, week_start):
        monkeypatch.setattr(service, "find_open_score_issue_id", find_open_issue_id)
        await solve_open_score_issues(measurable_id, week_start)
        return None

    async with signed_in_clients("u1") as clients:
        first = await clients["u1"].post(url)
        monkeypatch.setattr(service, "find_open_score_issue_id", solve_before_find)
        second = await clients["u1"].post(url)
    try:
        assert second.status_code == 201
        assert second.json()["id"] != first.json()["id"]
        assert await count_open_score_issues("m5", date(2026, 11, 2)) == 1
    finally:
        await delete_score_issues("m5", date(2026, 11, 2))
        await engine.dispose()


def open_score_issues(measurable_id, week_start):
    return (
        Issue.source_measurable_id == measurable_id,
        Issue.source_week_start == week_start,
        Issue.solved_at.is_(None),
    )


async def count_open_score_issues(measurable_id, week_start):
    async with SessionLocal() as session:
        return await session.scalar(select(func.count()).where(*open_score_issues(measurable_id, week_start)))


async def solve_open_score_issues(measurable_id, week_start):
    async with SessionLocal() as session:
        await session.execute(
            update(Issue)
            .where(*open_score_issues(measurable_id, week_start))
            .values(solved_at=utc_now(), resolution_note="Solved during the click")
        )
        await session.commit()


async def delete_score_issues(measurable_id, week_start):
    async with SessionLocal() as session:
        await session.execute(
            delete(Issue).where(Issue.source_measurable_id == measurable_id, Issue.source_week_start == week_start)
        )
        await session.commit()
