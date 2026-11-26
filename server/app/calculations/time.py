from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SCORECARD_WEEKS = 13


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def quarter_of(day: date) -> str:
    return f"{day.year}-Q{(day.month - 1) // 3 + 1}"


@dataclass(frozen=True)
class CompanyClock:
    now: datetime
    timezone: ZoneInfo

    def local_date(self, moment: datetime) -> date:
        return moment.astimezone(self.timezone).date()

    def start_of_day(self, day: date) -> datetime:
        return datetime.combine(day, time(), tzinfo=self.timezone).astimezone(UTC)

    @property
    def today(self) -> date:
        return self.local_date(self.now)

    @property
    def current_week(self) -> date:
        return week_start(self.today)

    @property
    def last_closed_week(self) -> date:
        return self.current_week - timedelta(weeks=1)

    @property
    def quarter(self) -> str:
        return quarter_of(self.today)

    @property
    def scorecard_weeks(self) -> list[date]:
        return [self.current_week - timedelta(weeks=offset) for offset in reversed(range(SCORECARD_WEEKS))]
