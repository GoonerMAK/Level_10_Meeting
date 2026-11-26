from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.columns import Timestamps, not_blank, pg_enum
from app.models.enums import UserRole


class Company(Timestamps, Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(Text)

    __table_args__ = (not_blank("name"),)


class Team(Timestamps, Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(Text)

    __table_args__ = (not_blank("name"),)


class User(Timestamps, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True)
    role: Mapped[UserRole] = mapped_column(pg_enum(UserRole, "user_role"))

    __table_args__ = (
        not_blank("name"),
        CheckConstraint("email = lower(email) AND position('@' in email) > 1", name="email_format"),
    )


class Membership(Timestamps, Base):
    __tablename__ = "memberships"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True, index=True)
