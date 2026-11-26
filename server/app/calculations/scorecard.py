import enum
from datetime import date
from decimal import Decimal

from app.models import Measurable
from app.models.enums import GoalType


class ScoreStatus(enum.StrEnum):
    ON_TRACK = "on_track"
    OFF_TRACK = "off_track"
    PENDING = "pending"


def meets_goal(measurable: Measurable, score: Decimal) -> bool:
    if measurable.goal_type is GoalType.BETWEEN:
        assert measurable.goal_min is not None and measurable.goal_max is not None
        return measurable.goal_min <= score <= measurable.goal_max
    assert measurable.goal_value is not None
    match measurable.goal_type:
        case GoalType.AT_LEAST:
            return score >= measurable.goal_value
        case GoalType.AT_MOST:
            return score <= measurable.goal_value
        case _:
            return score == measurable.goal_value


def score_status(measurable: Measurable, score: Decimal | None, week: date, current_week: date) -> ScoreStatus:
    if score is None:
        return ScoreStatus.PENDING if week >= current_week else ScoreStatus.OFF_TRACK
    return ScoreStatus.ON_TRACK if meets_goal(measurable, score) else ScoreStatus.OFF_TRACK
