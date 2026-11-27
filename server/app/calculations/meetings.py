from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.calculations.numbers import round_half_up
from app.models.enums import MeetingSection


def meeting_rating(ratings: Iterable[int]) -> Decimal | None:
    values = list(ratings)
    if not values:
        return None
    return round_half_up(Decimal(sum(values)) / len(values), 1)


@dataclass(frozen=True)
class SectionTimer:
    ends_at: datetime
    over_time: bool


AGENDA = (MeetingSection.SCORECARD, MeetingSection.IDS, MeetingSection.CONCLUDE)
SECTION_LENGTHS = {
    MeetingSection.SCORECARD: timedelta(minutes=5),
    MeetingSection.IDS: timedelta(minutes=60),
    MeetingSection.CONCLUDE: timedelta(minutes=10),
}


def section_after(section: MeetingSection) -> MeetingSection | None:
    position = AGENDA.index(section)
    return AGENDA[position + 1] if position + 1 < len(AGENDA) else None


def section_timer(section: MeetingSection, started_at: datetime, now: datetime) -> SectionTimer:
    ends_at = started_at + SECTION_LENGTHS[section]
    return SectionTimer(ends_at=ends_at, over_time=now > ends_at)
