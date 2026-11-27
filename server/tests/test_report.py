import asyncio
import json
from datetime import datetime

import pytest

from app.core.config import REPO_ROOT, settings
from app.report import build_report, freshly_seeded, report_database_url

SAVED_REPORT = REPO_ROOT / "rules_report.json"
NEXT_WEEK = datetime.fromisoformat("2026-11-18T15:00:00Z")
BEFORE_DAYLIGHT_SAVING_ENDS = datetime.fromisoformat("2026-10-30T15:00:00Z")


@pytest.fixture(scope="module")
def reports():
    async def build(*nows):
        async with freshly_seeded(report_database_url()) as sessions, sessions() as session:
            return [json.loads(json.dumps(await build_report(session, now))) for now in nows]

    default, next_week, before_dst = asyncio.run(build(settings.app_now, NEXT_WEEK, BEFORE_DAYLIGHT_SAVING_ENDS))
    return {"default": default, "next week": next_week, "before dst": before_dst}


def test_the_report_matches_the_saved_rules_report(reports):
    assert reports["default"] == json.loads(SAVED_REPORT.read_text(encoding="utf-8"))


def test_the_report_lists_every_team_with_13_weeks(reports):
    report = reports["default"]

    assert report["now"] == "2026-11-11T15:00:00Z"
    assert list(report["teams"]) == ["team_lead", "team_ops", "team_sales"]
    for team in report["teams"].values():
        assert len(team["todo_completion"]) == 13
        assert all(len(weeks) == 13 for weeks in team["measurable_status"].values())


def test_a_week_later_closes_last_week_and_moves_today(reports):
    lead = reports["next week"]["teams"]["team_lead"]

    assert reports["next week"]["now"] == "2026-11-18T15:00:00Z"
    assert list(lead["measurable_status"]["m1"])[0] == "2026-08-24"
    assert lead["measurable_status"]["m1"]["2026-11-09"] == "off_track"
    assert lead["measurable_status"]["m5"]["2026-11-09"] == "on_track"
    assert lead["measurable_status"]["m1"]["2026-11-16"] == "pending"
    assert lead["overdue_todos"] == ["t12", "t30", "t31", "t32"]
    assert lead["todo_completion"]["2026-11-09"] == {"due": 3, "done": 0, "rate_percent": 0, "meets_target": False}
    assert lead["rocks"]["r1"] == {"status": "off_track", "progress_percent": 33}
    assert reports["next week"]["teams"]["team_sales"]["overdue_todos"] == ["t40"]


def test_before_daylight_saving_ends_a_done_on_sunday_night_counts_in_time(reports):
    lead = reports["before dst"]["teams"]["team_lead"]

    assert list(lead["measurable_status"]["m1"])[:2] == ["2026-08-03", "2026-08-10"]
    assert lead["measurable_status"]["m1"]["2026-08-03"] == "off_track"
    assert lead["measurable_status"]["m5"]["2026-10-26"] == "on_track"
    assert lead["todo_completion"]["2026-10-26"] == {"due": 3, "done": 2, "rate_percent": 67, "meets_target": False}
    assert lead["overdue_todos"] == []
    assert lead["rocks"]["r1"]["status"] == lead["rocks"]["r2"]["status"] == "on_track"
