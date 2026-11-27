from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.columns import UtcTimestamp


class ClockStart(Base):
    __tablename__ = "clock_starts"

    app_now: Mapped[datetime] = mapped_column(UtcTimestamp, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(UtcTimestamp)
