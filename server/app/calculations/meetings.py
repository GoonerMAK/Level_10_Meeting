from collections.abc import Iterable
from decimal import Decimal

from app.calculations.numbers import round_half_up


def meeting_rating(ratings: Iterable[int]) -> Decimal | None:
    values = list(ratings)
    if not values:
        return None
    return round_half_up(Decimal(sum(values)) / len(values), 1)
