from decimal import ROUND_HALF_UP, Decimal


def round_half_up(value: Decimal, places: int = 0) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def whole_percent(part: int, total: int) -> int:
    return int(round_half_up(Decimal(part * 100) / total))
