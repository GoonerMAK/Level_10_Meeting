from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, SmallInteger, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.columns import Timestamps, UtcTimestamp, not_blank

if TYPE_CHECKING:
    from app.models.organization import User
    from app.models.scorecard import Measurable


class Issue(Timestamps, Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    priority: Mapped[int | None] = mapped_column(SmallInteger)
    solved_at: Mapped[datetime | None] = mapped_column(UtcTimestamp)
    resolution_note: Mapped[str | None] = mapped_column(Text)
    source_measurable_id: Mapped[str | None] = mapped_column(ForeignKey("measurables.id"))
    source_week_start: Mapped[date | None] = mapped_column(Date)

    owner: Mapped["User"] = relationship()
    source_measurable: Mapped["Measurable | None"] = relationship()

    __table_args__ = (
        not_blank("title"),
        CheckConstraint("priority BETWEEN 1 AND 5", name="priority_range"),
        CheckConstraint(
            "(solved_at IS NULL AND resolution_note IS NULL) "
            "OR (solved_at IS NOT NULL AND resolution_note IS NOT NULL AND length(trim(resolution_note)) > 0)",
            name="solved_requires_note",
        ),
        CheckConstraint("solved_at IS NULL OR solved_at >= created_at", name="solved_after_created"),
        CheckConstraint("(source_measurable_id IS NULL) = (source_week_start IS NULL)", name="source_complete"),
        CheckConstraint(
            "source_week_start IS NULL OR extract(isodow from source_week_start) = 1",
            name="source_week_is_monday",
        ),
        Index(
            "uq_issues_open_source",
            "source_measurable_id",
            "source_week_start",
            unique=True,
            postgresql_where=text("solved_at IS NULL AND source_measurable_id IS NOT NULL"),
        ),
        Index("ix_issues_team_open", "team_id", postgresql_where=text("solved_at IS NULL")),
    )
