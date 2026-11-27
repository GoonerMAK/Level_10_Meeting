from collections.abc import Sequence
from datetime import date
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.calculations.issues import in_issue_order, score_issue_title
from app.calculations.scorecard import ScoreStatus, score_status
from app.core.clock import utc_now
from app.core.errors import Conflict, NotFound
from app.core.permissions import CurrentUser
from app.models import Issue, Measurable
from app.models.enums import AuditAction, AuditEntity
from app.modules.activity.service import Changed, record
from app.modules.issues.schemas import IssueState
from app.modules.live.hub import publish_change
from app.modules.scorecard.service import ensure_scorecard_week, get_changeable_measurable, get_score_value
from app.modules.teams.service import company_clock, get_changeable_row, get_changeable_team, get_readable_team

ISSUE_DETAILS = (selectinload(Issue.owner), selectinload(Issue.source_measurable))
SCORE_ISSUE_ATTEMPTS = 3


async def load_issue(session: AsyncSession, issue_id: str) -> Issue:
    issue = await session.scalar(select(Issue).where(Issue.id == issue_id).options(*ISSUE_DETAILS))
    if issue is None:
        raise NotFound("Issue not found")
    return issue


async def get_changeable_open_issue(session: AsyncSession, current_user: CurrentUser, issue_id: str) -> Issue:
    issue = await get_changeable_row(session, current_user, Issue, issue_id, "Issue")
    if issue.solved_at is not None:
        raise Conflict("This Issue is already solved")
    return issue


async def list_issues(session: AsyncSession, current_user: CurrentUser, team_id: str, state: IssueState) -> Sequence[Issue]:
    await get_readable_team(session, current_user, team_id)
    solved = Issue.solved_at.is_not(None) if state == "solved" else Issue.solved_at.is_(None)
    issues = (await session.scalars(select(Issue).where(Issue.team_id == team_id, solved).options(*ISSUE_DETAILS))).all()
    if state == "solved":
        return sorted(issues, key=lambda issue: (issue.solved_at, issue.id), reverse=True)
    return in_issue_order(issues)


async def create_issue(
    session: AsyncSession, current_user: CurrentUser, team_id: str, title: str, priority: int | None
) -> Issue:
    await get_changeable_team(session, current_user, team_id)
    issue = Issue(id=str(uuid4()), team_id=team_id, title=title, owner_id=current_user.id, priority=priority)
    session.add(issue)
    record_issue(session, current_user, issue, AuditAction.CREATED, [("title", None, title), ("priority", None, priority)])
    await session.commit()
    await publish_change(team_id, "issues")
    return await load_issue(session, issue.id)


async def create_issue_from_score(
    session: AsyncSession, current_user: CurrentUser, measurable_id: str, week_start: date
) -> tuple[Issue, bool]:
    measurable = await get_changeable_measurable(session, current_user, measurable_id)
    clock = await company_clock(session, measurable.team_id)
    ensure_scorecard_week(clock, week_start)
    value = await get_score_value(session, measurable_id, week_start)
    if score_status(measurable, value, week_start, clock.current_week) is not ScoreStatus.OFF_TRACK:
        raise Conflict("Only off-track scores can become an Issue")
    for _ in range(SCORE_ISSUE_ATTEMPTS):
        created_id = await insert_score_issue(session, current_user, measurable, week_start, clock.today)
        if created_id is not None:
            await publish_change(measurable.team_id, "issues")
            return await load_issue(session, created_id), True
        existing_id = await find_open_score_issue_id(session, measurable_id, week_start)
        if existing_id is not None:
            return await load_issue(session, existing_id), False
    raise Conflict("This score's Issue changed while it was being made. Try again")


async def insert_score_issue(
    session: AsyncSession, current_user: CurrentUser, measurable: Measurable, week_start: date, today: date
) -> str | None:
    statement = (
        insert(Issue)
        .values(
            id=str(uuid4()),
            team_id=measurable.team_id,
            title=score_issue_title(measurable.name, week_start, today),
            owner_id=current_user.id,
            source_measurable_id=measurable.id,
            source_week_start=week_start,
        )
        .on_conflict_do_nothing(
            index_elements=[Issue.source_measurable_id, Issue.source_week_start],
            index_where=Issue.solved_at.is_(None) & Issue.source_measurable_id.is_not(None),
        )
        .returning(Issue.id)
    )
    created_id = await session.scalar(statement)
    if created_id is not None:
        record(
            session,
            user_id=current_user.id,
            team_id=measurable.team_id,
            entity=AuditEntity.ISSUE,
            entity_id=created_id,
            label=score_issue_title(measurable.name, week_start, today),
            action=AuditAction.CREATED,
            changes=[("source", None, f"{measurable.id}:{week_start}")],
        )
    await session.commit()
    return created_id


def record_issue(
    session: AsyncSession, current_user: CurrentUser, issue: Issue, action: AuditAction, changes: list[Changed]
) -> None:
    record(
        session,
        user_id=current_user.id,
        team_id=issue.team_id,
        entity=AuditEntity.ISSUE,
        entity_id=issue.id,
        label=issue.title,
        action=action,
        changes=changes,
    )


async def find_open_score_issue_id(session: AsyncSession, measurable_id: str, week_start: date) -> str | None:
    return await session.scalar(
        select(Issue.id).where(
            Issue.source_measurable_id == measurable_id,
            Issue.source_week_start == week_start,
            Issue.solved_at.is_(None),
        )
    )


async def set_priority(session: AsyncSession, current_user: CurrentUser, issue_id: str, priority: int | None) -> Issue:
    issue = await get_changeable_open_issue(session, current_user, issue_id)
    if issue.priority != priority:
        record_issue(session, current_user, issue, AuditAction.UPDATED, [("priority", issue.priority, priority)])
    issue.priority = priority
    await session.commit()
    await publish_change(issue.team_id, "issues")
    return await load_issue(session, issue_id)


async def solve_issue(session: AsyncSession, current_user: CurrentUser, issue_id: str, resolution_note: str) -> Issue:
    issue = await get_changeable_open_issue(session, current_user, issue_id)
    issue.solved_at = utc_now()
    issue.resolution_note = resolution_note
    record_issue(session, current_user, issue, AuditAction.SOLVED, [("resolution_note", None, resolution_note)])
    await session.commit()
    await publish_change(issue.team_id, "issues")
    return await load_issue(session, issue_id)
