from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.calculations.scorecard import score_status
from app.calculations.time import CompanyClock
from app.core.clock import utc_now
from app.core.errors import InvalidInput
from app.core.permissions import CurrentUser
from app.core.schemas import UserRef
from app.models import Measurable, Score
from app.modules.scorecard.schemas import Goal, MeasurableRow, Scorecard, ScoreCell
from app.modules.teams.service import company_clock, get_changeable_row, readable_team_clock


async def get_changeable_measurable(session: AsyncSession, current_user: CurrentUser, measurable_id: str) -> Measurable:
    return await get_changeable_row(session, current_user, Measurable, measurable_id, "Measurable")


def ensure_scorecard_week(clock: CompanyClock, week_start: date) -> None:
    if week_start not in clock.scorecard_weeks:
        raise InvalidInput("Scores can only be entered for the last 13 weeks, as a Monday", "week_start")


async def get_score_value(session: AsyncSession, measurable_id: str, week_start: date) -> Decimal | None:
    return await session.scalar(
        select(Score.value).where(Score.measurable_id == measurable_id, Score.week_start == week_start)
    )


def score_cell(measurable: Measurable, week_start: date, value: Decimal | None, clock: CompanyClock) -> ScoreCell:
    return ScoreCell(week_start=week_start, value=value, status=score_status(measurable, value, week_start, clock.current_week))


async def get_scorecard(session: AsyncSession, current_user: CurrentUser, team_id: str) -> Scorecard:
    clock = await readable_team_clock(session, current_user, team_id)
    weeks = clock.scorecard_weeks
    measurables = (
        await session.scalars(
            select(Measurable).where(Measurable.team_id == team_id).options(selectinload(Measurable.owner)).order_by(Measurable.id)
        )
    ).all()
    scores = await session.execute(
        select(Score.measurable_id, Score.week_start, Score.value).where(
            Score.measurable_id.in_([measurable.id for measurable in measurables]),
            Score.week_start.between(weeks[0], weeks[-1]),
        )
    )
    values = {(measurable_id, week): value for measurable_id, week, value in scores}
    rows = [
        MeasurableRow(
            id=measurable.id,
            name=measurable.name,
            owner=UserRef.model_validate(measurable.owner),
            unit=measurable.unit,
            goal=Goal(type=measurable.goal_type, value=measurable.goal_value, min=measurable.goal_min, max=measurable.goal_max),
            cells=[score_cell(measurable, week, values.get((measurable.id, week)), clock) for week in weeks],
        )
        for measurable in measurables
    ]
    return Scorecard(weeks=weeks, current_week=clock.current_week, measurables=rows)


async def set_score(
    session: AsyncSession, current_user: CurrentUser, measurable_id: str, week_start: date, value: Decimal
) -> ScoreCell:
    measurable = await get_changeable_measurable(session, current_user, measurable_id)
    clock = await company_clock(session, measurable.team_id)
    ensure_scorecard_week(clock, week_start)
    statement = insert(Score).values(
        measurable_id=measurable_id, week_start=week_start, value=value, updated_by_id=current_user.id
    )
    await session.execute(
        statement.on_conflict_do_update(
            index_elements=[Score.measurable_id, Score.week_start],
            set_={"value": value, "updated_by_id": current_user.id, "updated_at": utc_now()},
        )
    )
    await session.commit()
    return score_cell(measurable, week_start, value, clock)
