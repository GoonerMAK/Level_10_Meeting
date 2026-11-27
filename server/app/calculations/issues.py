from collections.abc import Iterable
from datetime import date, datetime

from app.models import Issue


def issue_order_key(issue: Issue) -> tuple[bool, int, datetime, str]:
    return (issue.priority is None, -(issue.priority or 0), issue.created_at, issue.id)


def in_issue_order(issues: Iterable[Issue]) -> list[Issue]:
    return sorted(issues, key=issue_order_key)


def score_issue_title(measurable_name: str, week: date, today: date) -> str:
    year = "" if week.year == today.year else f", {week.year}"
    return f"{measurable_name}, week of {week:%b} {week.day}{year}"
