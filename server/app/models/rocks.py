from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.columns import Timestamps, not_blank, pg_enum
from app.models.enums import RockStatus

if TYPE_CHECKING:
    from app.models.organization import User


class Rock(Timestamps, Base):
    __tablename__ = "rocks"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    quarter: Mapped[str] = mapped_column(Text, index=True)
    status: Mapped[RockStatus] = mapped_column(pg_enum(RockStatus, "rock_status"))

    owner: Mapped["User"] = relationship()
    milestones: Mapped[list["Milestone"]] = relationship(order_by="(Milestone.due_date, Milestone.id)")

    __table_args__ = (
        not_blank("title"),
        CheckConstraint("quarter ~ '^[0-9]{4}-Q[1-4]$'", name="quarter_format"),
    )


class Milestone(Timestamps, Base):
    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    rock_id: Mapped[str] = mapped_column(ForeignKey("rocks.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date] = mapped_column(Date)
    done: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    __table_args__ = (not_blank("title"),)
