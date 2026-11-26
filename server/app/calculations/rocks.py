from collections.abc import Sequence
from datetime import date

from app.calculations.numbers import whole_percent
from app.models import Milestone
from app.models.enums import RockStatus


def rock_status(seeded_status: RockStatus, milestones: Sequence[Milestone], today: date) -> RockStatus:
    if seeded_status is RockStatus.COMPLETE:
        return RockStatus.COMPLETE
    if seeded_status is RockStatus.OFF_TRACK or any(not item.done and item.due_date < today for item in milestones):
        return RockStatus.OFF_TRACK
    return RockStatus.ON_TRACK


def rock_progress(seeded_status: RockStatus, milestones: Sequence[Milestone]) -> int:
    if not milestones:
        return 100 if seeded_status is RockStatus.COMPLETE else 0
    return whole_percent(sum(1 for item in milestones if item.done), len(milestones))
