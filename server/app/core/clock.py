from datetime import UTC, datetime, timedelta

from app.core.config import settings


class TickingClock:
    def __init__(self, app_now: datetime, real_start: datetime) -> None:
        self.offset = real_start - app_now

    def now(self) -> datetime:
        return datetime.now(UTC) - self.offset


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


Clock = TickingClock | FixedClock
installed_clock: Clock = TickingClock(settings.app_now, datetime.now(UTC))


def use_clock(clock: Clock) -> None:
    global installed_clock
    installed_clock = clock


def calendar_now() -> datetime:
    return settings.app_now


def utc_now() -> datetime:
    return installed_clock.now()
