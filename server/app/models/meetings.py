from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, SmallInteger, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.columns import UtcTimestamp, pg_enum
from app.models.enums import MeetingSection


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    facilitator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(UtcTimestamp)
    ended_at: Mapped[datetime | None] = mapped_column(UtcTimestamp)
    current_section: Mapped[MeetingSection | None] = mapped_column(pg_enum(MeetingSection, "meeting_section"))
    section_started_at: Mapped[datetime | None] = mapped_column(UtcTimestamp)

    __table_args__ = (
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ended_after_started"),
        CheckConstraint(
            "(ended_at IS NULL AND current_section IS NOT NULL AND section_started_at IS NOT NULL) "
            "OR (ended_at IS NOT NULL AND current_section IS NULL AND section_started_at IS NULL)",
            name="active_has_section",
        ),
        Index("uq_meetings_one_active_per_team", "team_id", unique=True, postgresql_where=text("ended_at IS NULL")),
    )


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"

    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime | None] = mapped_column(UtcTimestamp)


class MeetingRating(Base):
    __tablename__ = "meeting_ratings"

    meeting_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    rating: Mapped[int] = mapped_column(SmallInteger)
    rated_at: Mapped[datetime | None] = mapped_column(UtcTimestamp)

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 10", name="rating_range"),
        ForeignKeyConstraint(
            ["meeting_id", "user_id"],
            ["meeting_attendees.meeting_id", "meeting_attendees.user_id"],
            ondelete="CASCADE",
            name="fk_meeting_ratings_attendee",
        ),
    )
