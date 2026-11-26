from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.columns import Timestamps, pg_enum
from app.models.enums import GoalType


class Measurable(Timestamps, Base):
    __tablename__ = "measurables"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    unit: Mapped[str] = mapped_column(Text)
    goal_type: Mapped[GoalType] = mapped_column(pg_enum(GoalType, "goal_type"))
    goal_value: Mapped[Decimal | None] = mapped_column(Numeric)
    goal_min: Mapped[Decimal | None] = mapped_column(Numeric)
    goal_max: Mapped[Decimal | None] = mapped_column(Numeric)

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="name_not_blank"),
        CheckConstraint(
            "(goal_type = 'between' AND goal_value IS NULL AND goal_min IS NOT NULL "
            "AND goal_max IS NOT NULL AND goal_min <= goal_max) "
            "OR (goal_type <> 'between' AND goal_value IS NOT NULL AND goal_min IS NULL AND goal_max IS NULL)",
            name="goal_shape",
        ),
    )


class Score(Timestamps, Base):
    __tablename__ = "scores"

    measurable_id: Mapped[str] = mapped_column(ForeignKey("measurables.id", ondelete="CASCADE"), primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric)
    updated_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (CheckConstraint("extract(isodow from week_start) = 1", name="week_start_is_monday"),)
