from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.columns import Timestamps, UtcTimestamp, not_blank

if TYPE_CHECKING:
    from app.models.issues import Issue
    from app.models.organization import User


class Todo(Timestamps, Base):
    __tablename__ = "todos"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    done_at: Mapped[datetime | None] = mapped_column(UtcTimestamp)
    source_issue_id: Mapped[str | None] = mapped_column(ForeignKey("issues.id", ondelete="SET NULL"), index=True)

    owner: Mapped["User"] = relationship()
    source_issue: Mapped["Issue | None"] = relationship()

    __table_args__ = (not_blank("title"),)
