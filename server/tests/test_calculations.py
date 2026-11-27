from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.calculations.issues import in_issue_order, score_issue_title
from app.calculations.meetings import meeting_rating, section_after, section_timer
from app.calculations.numbers import whole_percent
from app.calculations.rocks import rock_progress, rock_status
from app.calculations.scorecard import ScoreStatus, score_status
from app.calculations.time import CompanyClock
from app.calculations.todos import completion_for_week, is_overdue
from app.models import Issue, Measurable, Milestone, Todo
from app.models.enums import GoalType, MeetingSection, RockStatus

CHICAGO = ZoneInfo("America/Chicago")
CLOCK = CompanyClock(now=datetime(2026, 11, 11, 15, 0, tzinfo=UTC), timezone=CHICAGO)
CURRENT_WEEK = date(2026, 11, 9)
CLOSED_WEEK = date(2026, 11, 2)


def test_clock_reads_weeks_and_quarter_in_company_time():
    assert (CLOCK.today, CLOCK.current_week, CLOCK.last_closed_week, CLOCK.quarter) == (
        date(2026, 11, 11),
        CURRENT_WEEK,
        CLOSED_WEEK,
        "2026-Q4",
    )
    assert (CLOCK.scorecard_weeks[0], CLOCK.scorecard_weeks[-1], len(CLOCK.scorecard_weeks)) == (
        date(2026, 8, 17),
        CURRENT_WEEK,
        13,
    )


@pytest.mark.parametrize(
    ("last_second", "monday", "week_before", "monday_midnight_utc"),
    [
        (datetime(2026, 11, 2, 5, 59, 59, tzinfo=UTC), date(2026, 11, 2), date(2026, 10, 26), datetime(2026, 11, 2, 6, tzinfo=UTC)),
        (datetime(2026, 3, 9, 4, 59, 59, tzinfo=UTC), date(2026, 3, 9), date(2026, 3, 2), datetime(2026, 3, 9, 5, tzinfo=UTC)),
    ],
    ids=["after daylight saving ends", "after daylight saving starts"],
)
def test_the_week_turns_at_monday_midnight_across_a_daylight_saving_change(last_second, monday, week_before, monday_midnight_utc):
    sunday_night = CompanyClock(now=last_second, timezone=CHICAGO)
    monday_start = CompanyClock(now=last_second + timedelta(seconds=1), timezone=CHICAGO)

    assert (sunday_night.current_week, monday_start.current_week) == (week_before, monday)
    assert sunday_night.start_of_day(monday) == monday_midnight_utc
    weeks = monday_start.scorecard_weeks
    assert len(weeks) == 13
    assert all(week.weekday() == 0 for week in weeks)
    assert all(later - earlier == timedelta(weeks=1) for earlier, later in pairwise(weeks))


def test_week_boundary_is_monday_midnight_in_company_time():
    sunday_night = CompanyClock(now=datetime(2026, 11, 9, 5, 59, 59, tzinfo=UTC), timezone=CHICAGO)
    monday_start = CompanyClock(now=datetime(2026, 11, 9, 6, 0, 0, tzinfo=UTC), timezone=CHICAGO)
    assert (sunday_night.current_week, monday_start.current_week) == (CLOSED_WEEK, CURRENT_WEEK)


@pytest.mark.parametrize(
    ("goal", "score", "expected"),
    [
        ({"goal_type": GoalType.AT_LEAST, "goal_value": Decimal(10)}, Decimal(10), ScoreStatus.ON_TRACK),
        ({"goal_type": GoalType.AT_LEAST, "goal_value": Decimal(10)}, Decimal("9.99"), ScoreStatus.OFF_TRACK),
        ({"goal_type": GoalType.AT_MOST, "goal_value": Decimal(5)}, Decimal(5), ScoreStatus.ON_TRACK),
        ({"goal_type": GoalType.AT_MOST, "goal_value": Decimal(5)}, Decimal("5.01"), ScoreStatus.OFF_TRACK),
        ({"goal_type": GoalType.BETWEEN, "goal_min": Decimal(2), "goal_max": Decimal(4)}, Decimal(2), ScoreStatus.ON_TRACK),
        ({"goal_type": GoalType.BETWEEN, "goal_min": Decimal(2), "goal_max": Decimal(4)}, Decimal(4), ScoreStatus.ON_TRACK),
        ({"goal_type": GoalType.BETWEEN, "goal_min": Decimal(2), "goal_max": Decimal(4)}, Decimal("4.1"), ScoreStatus.OFF_TRACK),
        ({"goal_type": GoalType.EXACTLY, "goal_value": Decimal(3)}, Decimal(3), ScoreStatus.ON_TRACK),
        ({"goal_type": GoalType.EXACTLY, "goal_value": Decimal(3)}, Decimal("3.5"), ScoreStatus.OFF_TRACK),
    ],
)
def test_measurable_status_counts_boundaries_as_on_track(goal, score, expected):
    assert score_status(Measurable(**goal), score, CLOSED_WEEK, CURRENT_WEEK) is expected


def test_missing_score_is_off_track_when_closed_and_pending_when_current():
    measurable = Measurable(goal_type=GoalType.AT_LEAST, goal_value=Decimal(10))
    assert score_status(measurable, None, CLOSED_WEEK, CURRENT_WEEK) is ScoreStatus.OFF_TRACK
    assert score_status(measurable, None, CURRENT_WEEK, CURRENT_WEEK) is ScoreStatus.PENDING


def todo(due: date, done_at: datetime | None = None) -> Todo:
    return Todo(due_date=due, done_at=done_at)


def test_todo_due_today_is_not_overdue():
    assert not is_overdue(todo(date(2026, 11, 11)), CLOCK.today)
    assert is_overdue(todo(date(2026, 11, 10)), CLOCK.today)
    assert not is_overdue(todo(date(2026, 11, 10), done_at=CLOCK.now), CLOCK.today)


def test_completion_rate_of_exactly_90_percent_meets_target():
    sunday_night = datetime(2026, 11, 9, 5, 59, 59, tzinfo=UTC)
    todos = [todo(date(2026, 11, 6), done_at=sunday_night) for _ in range(9)] + [todo(date(2026, 11, 6))]
    completion = completion_for_week(todos, CLOSED_WEEK, CLOCK)
    assert completion is not None
    assert (completion.due, completion.done, completion.rate_percent, completion.meets_target) == (10, 9, 90, True)


def test_completion_counts_done_after_due_week_as_not_done_and_rounds_half_up():
    monday_after = datetime(2026, 11, 9, 6, 0, 0, tzinfo=UTC)
    on_time = datetime(2026, 11, 5, 15, 0, tzinfo=UTC)
    todos = [todo(date(2026, 11, 4), done_at=on_time)] + [todo(date(2026, 11, 4), done_at=monday_after) for _ in range(7)]
    completion = completion_for_week(todos, CLOSED_WEEK, CLOCK)
    assert completion is not None
    assert (completion.done, completion.rate_percent, completion.meets_target) == (1, 13, False)


def test_week_with_no_todos_due_has_no_rate():
    assert completion_for_week([todo(date(2026, 11, 12))], CLOSED_WEEK, CLOCK) is None


def milestone(due: date, done: bool) -> Milestone:
    return Milestone(due_date=due, done=done)


def test_rock_status_milestone_due_today_is_not_past_due():
    assert rock_status(RockStatus.ON_TRACK, [milestone(CLOCK.today, False)], CLOCK.today) is RockStatus.ON_TRACK
    assert rock_status(RockStatus.ON_TRACK, [milestone(date(2026, 11, 10), False)], CLOCK.today) is RockStatus.OFF_TRACK
    assert rock_status(RockStatus.ON_TRACK, [milestone(date(2026, 11, 10), True)], CLOCK.today) is RockStatus.ON_TRACK


def test_rock_status_seeded_complete_and_off_track_win():
    assert rock_status(RockStatus.COMPLETE, [milestone(date(2026, 11, 1), False)], CLOCK.today) is RockStatus.COMPLETE
    assert rock_status(RockStatus.OFF_TRACK, [], CLOCK.today) is RockStatus.OFF_TRACK
    assert rock_status(RockStatus.ON_TRACK, [], CLOCK.today) is RockStatus.ON_TRACK


def test_rock_progress_rounds_half_up_and_handles_no_milestones():
    eight = [milestone(CLOCK.today, index == 0) for index in range(8)]
    assert rock_progress(RockStatus.ON_TRACK, eight) == 13
    assert rock_progress(RockStatus.ON_TRACK, []) == 0
    assert rock_progress(RockStatus.COMPLETE, []) == 100


def test_whole_percent_rounds_half_up():
    assert (whole_percent(1, 8), whole_percent(2, 3), whole_percent(1, 3)) == (13, 67, 33)


def test_issue_order_is_priority_high_first_then_oldest_with_no_priority_last():
    older = datetime(2026, 11, 1, tzinfo=UTC)
    newer = datetime(2026, 11, 2, tzinfo=UTC)
    issues = [
        Issue(id="none", priority=None, created_at=older),
        Issue(id="p3_newer", priority=3, created_at=newer),
        Issue(id="p5", priority=5, created_at=newer),
        Issue(id="p3_older", priority=3, created_at=older),
        Issue(id="p1", priority=1, created_at=older),
    ]
    assert [issue.id for issue in in_issue_order(issues)] == ["p5", "p3_older", "p3_newer", "p1", "none"]


def test_score_issue_title_matches_the_seed_and_adds_the_year_only_for_another_year():
    assert score_issue_title("New deals closed", date(2026, 11, 2), CLOCK.today) == "New deals closed, week of Nov 2"
    assert score_issue_title("Payroll runs", date(2025, 12, 29), date(2026, 1, 5)) == "Payroll runs, week of Dec 29, 2025"


def test_meeting_rating_averages_to_one_decimal_half_up():
    assert meeting_rating([8, 9, 8, 8]) == Decimal("8.3")
    assert meeting_rating([7]) == Decimal("7.0")
    assert meeting_rating([]) is None


def test_the_agenda_runs_scorecard_then_ids_then_conclude():
    assert section_after(MeetingSection.SCORECARD) is MeetingSection.IDS
    assert section_after(MeetingSection.IDS) is MeetingSection.CONCLUDE
    assert section_after(MeetingSection.CONCLUDE) is None


@pytest.mark.parametrize(
    ("section", "minutes"),
    [(MeetingSection.SCORECARD, 5), (MeetingSection.IDS, 60), (MeetingSection.CONCLUDE, 10)],
)
def test_a_section_is_over_time_only_after_its_length(section, minutes):
    started_at = datetime(2026, 11, 11, 15, 0, tzinfo=UTC)
    ends_at = started_at + timedelta(minutes=minutes)

    assert section_timer(section, started_at, ends_at).ends_at == ends_at
    assert section_timer(section, started_at, ends_at).over_time is False
    assert section_timer(section, started_at, ends_at + timedelta(seconds=1)).over_time is True
