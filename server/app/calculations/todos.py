from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction

from app.calculations.numbers import whole_percent
from app.calculations.time import CompanyClock
from app.models import Todo

COMPLETION_TARGET = Fraction(9, 10)


@dataclass(frozen=True)
class Completion:
    due: int
    done: int
    rate_percent: int
    meets_target: bool


def is_overdue(todo: Todo, today: date) -> bool:
    return todo.done_at is None and todo.due_date < today


def completion_for_week(todos: Iterable[Todo], week: date, clock: CompanyClock) -> Completion | None:
    week_end = week + timedelta(days=6)
    due = [todo for todo in todos if week <= todo.due_date <= week_end]
    if not due:
        return None
    done = sum(1 for todo in due if todo.done_at is not None and clock.local_date(todo.done_at) <= week_end)
    return Completion(
        due=len(due),
        done=done,
        rate_percent=whole_percent(done, len(due)),
        meets_target=Fraction(done, len(due)) >= COMPLETION_TARGET,
    )
