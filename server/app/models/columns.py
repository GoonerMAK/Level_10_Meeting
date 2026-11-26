import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utc_now

UtcTimestamp = DateTime(timezone=True)


def pg_enum(enum_class: type[enum.Enum], name: str) -> Enum:
    return Enum(enum_class, name=name, values_callable=lambda members: [member.value for member in members])


def not_blank(column: str) -> CheckConstraint:
    return CheckConstraint(f"length(trim({column})) > 0", name=f"{column}_not_blank")


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(UtcTimestamp, default=utc_now, sort_order=100)
    updated_at: Mapped[datetime] = mapped_column(UtcTimestamp, default=utc_now, onupdate=utc_now, sort_order=101)
