import pytest
from sqlalchemy import update

from app.db.session import SessionLocal, engine
from app.models import Measurable


def test_rocks_are_listed_by_owner_then_title(sign_in):
    rocks = sign_in("u2").get("/api/teams/team_lead/rocks").json()["rocks"]

    assert [(rock["owner"]["name"], rock["title"]) for rock in rocks] == [
        ("Blake Brooks", "Launch partner portal"),
        ("Blake Brooks", "Refresh brand"),
        ("Casey Cho", "Hire VP of Sales"),
        ("Casey Cho", "Q4 pricing review"),
        ("Dana Diaz", "ERP migration"),
    ]


def test_seeded_measurables_keep_the_seed_order(sign_in):
    scorecard = sign_in("u2").get("/api/teams/team_lead/scorecard").json()

    assert [row["name"] for row in scorecard["measurables"]] == [
        "New deals closed",
        "Customer churn",
        "Avg first response",
        "Payroll runs",
        "Cash on hand",
    ]


async def set_position(measurable_id, position):
    async with SessionLocal() as session:
        await session.execute(update(Measurable).where(Measurable.id == measurable_id).values(position=position))
        await session.commit()


@pytest.mark.anyio
async def test_measurables_follow_their_position_on_the_scorecard_and_summary(signed_in_clients):
    await set_position("m5", 0)
    try:
        async with signed_in_clients("u2") as clients:
            scorecard = (await clients["u2"].get("/api/teams/team_lead/scorecard")).json()
            summary = (await clients["u2"].get("/api/meetings/mt2/summary")).json()
    finally:
        await set_position("m5", 5)
        await engine.dispose()

    expected = ["m5", "m1", "m2", "m3", "m4"]
    assert [row["id"] for row in scorecard["measurables"]] == expected
    assert [row["id"] for row in summary["measurables"]] == expected
