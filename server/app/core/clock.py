from datetime import datetime, timedelta
from time import monotonic

from app.core.config import settings


class TickingClock:
    def __init__(self, resume_from: datetime) -> None:
        self.resume_from = resume_from
        self.started = monotonic()

    def now(self) -> datetime:
        return self.resume_from + timedelta(seconds=monotonic() - self.started)


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


Clock = TickingClock | FixedClock
installed_clock: Clock = TickingClock(settings.app_now)


def use_clock(clock: Clock) -> None:
    global installed_clock
    installed_clock = clock


def calendar_now() -> datetime:
    return settings.app_now


def utc_now() -> datetime:
    return installed_clock.now()
