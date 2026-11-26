from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.columns import UtcTimestamp


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True) 
    title: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    done_at: Mapped[datetime | None] = mapped_column(UtcTimestamp)
    source_issue_id: Mapped[str | None] = mapped_column(ForeignKey("issues.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[datetime] = mapped_column(UtcTimestamp)
    updated_at: Mapped[datetime | None] = mapped_column(UtcTimestamp)

    __table_args__ = (CheckConstraint("length(trim(title)) > 0", name="title_not_blank"),)
