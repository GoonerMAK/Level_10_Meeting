from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.calculations.scorecard import ScoreStatus
from app.core.schemas import JsonNumber, UserRef
from app.models.enums import GoalType


class Goal(BaseModel):
    type: GoalType
    value: JsonNumber | None
    min: JsonNumber | None
    max: JsonNumber | None


class ScoreCell(BaseModel):
    week_start: date
    value: JsonNumber | None
    status: ScoreStatus


class MeasurableRow(BaseModel):
    id: str
    name: str
    owner: UserRef
    unit: str
    goal: Goal
    cells: list[ScoreCell]


class Scorecard(BaseModel):
    weeks: list[date]
    current_week: date
    measurables: list[MeasurableRow]


class ScoreUpdate(BaseModel):
    value: Decimal = Field(max_digits=15, decimal_places=4)
