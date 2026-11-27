from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.columns import UtcTimestamp


class AppClock(Base):
    __tablename__ = "app_clocks"

    app_now: Mapped[datetime] = mapped_column(UtcTimestamp, primary_key=True)
    reached_at: Mapped[datetime] = mapped_column(UtcTimestamp)
