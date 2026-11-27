from typing import Any
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculations.meetings import AGENDA, section_after, section_timer
from app.core.clock import utc_now
from app.core.errors import Conflict, Forbidden, NotFound
from app.core.permissions import CurrentUser, ensure_can_read_team
from app.core.schemas import UserRef
from app.db.session import SessionLocal
from app.models import Meeting, MeetingAttendee, MeetingRating, User
from app.models.enums import MeetingSection, UserRole
from app.modules.live.hub import current_hub
from app.modules.meetings.schemas import MeetingRatingOut, MeetingState
from app.modules.teams.service import get_readable_team

START_ATTEMPTS = 3
ACTIVE = Meeting.ended_at.is_(None)


async def start_meeting(session: AsyncSession, current_user: CurrentUser, team_id: str) -> tuple[MeetingState, bool]:
    await get_readable_team(session, current_user, team_id)
    if current_user.role is UserRole.OBSERVER:
        raise Forbidden("Observers can join meetings but cannot start them")
    for _ in range(START_ATTEMPTS):
        created_id = await insert_meeting(session, current_user, team_id)
        if created_id is not None:
            return await join_meeting_by_id(session, current_user, created_id), True
        active_id = await find_active_meeting_id(session, team_id)
        if active_id is not None:
            return await join_meeting_by_id(session, current_user, active_id), False
    raise Conflict("The team's meeting changed while it was being started. Try again")


async def insert_meeting(session: AsyncSession, current_user: CurrentUser, team_id: str) -> str | None:
    now = utc_now()
    statement = (
        insert(Meeting)
        .values(
            id=str(uuid4()),
            team_id=team_id,
            facilitator_id=current_user.id,
            started_at=now,
            current_section=AGENDA[0],
            section_started_at=now,
        )
        .on_conflict_do_nothing(index_elements=[Meeting.team_id], index_where=ACTIVE)
        .returning(Meeting.id)
    )
    created_id = await session.scalar(statement)
    await session.commit()
    return created_id


async def find_active_meeting_id(session: AsyncSession, team_id: str) -> str | None:
    return await session.scalar(select(Meeting.id).where(Meeting.team_id == team_id, ACTIVE))


async def get_active_meeting(session: AsyncSession, current_user: CurrentUser, team_id: str) -> MeetingState:
    await get_readable_team(session, current_user, team_id)
    active_id = await find_active_meeting_id(session, team_id)
    if active_id is None:
        raise NotFound("This team has no meeting running")
    return await meeting_state(session, await load_meeting(session, active_id))


async def get_meeting(session: AsyncSession, current_user: CurrentUser, meeting_id: str) -> MeetingState:
    return await meeting_state(session, await get_readable_meeting(session, current_user, meeting_id))


async def join_meeting(session: AsyncSession, current_user: CurrentUser, meeting_id: str) -> MeetingState:
    await get_readable_meeting(session, current_user, meeting_id)
    return await join_meeting_by_id(session, current_user, meeting_id)


async def join_meeting_by_id(session: AsyncSession, current_user: CurrentUser, meeting_id: str) -> MeetingState:
    meeting = await load_meeting(session, meeting_id)
    ensure_running(meeting)
    joined = await session.scalar(
        insert(MeetingAttendee)
        .values(meeting_id=meeting_id, user_id=current_user.id, joined_at=utc_now())
        .on_conflict_do_nothing(index_elements=[MeetingAttendee.meeting_id, MeetingAttendee.user_id])
        .returning(MeetingAttendee.user_id)
    )
    await session.commit()
    if joined is not None:
        await publish_meeting(meeting.team_id, meeting_id)
    return await meeting_state(session, meeting)


async def move_to_next_section(
    session: AsyncSession, current_user: CurrentUser, meeting_id: str, from_section: MeetingSection
) -> MeetingState:
    meeting = await get_facilitated_meeting(session, current_user, meeting_id)
    if meeting.current_section is not from_section:
        raise Conflict("The meeting has already moved on")
    following = section_after(from_section)
    if following is None:
        raise Conflict("Conclude is the last section. End the meeting instead")
    moved = await session.scalar(
        update(Meeting)
        .where(Meeting.id == meeting_id, ACTIVE, Meeting.current_section == from_section)
        .values(current_section=following, section_started_at=utc_now())
        .returning(Meeting.id)
    )
    await session.commit()
    if moved is None:
        raise Conflict("The meeting has already moved on")
    await publish_meeting(meeting.team_id, meeting_id)
    return await meeting_state(session, await load_meeting(session, meeting_id))


async def end_meeting(session: AsyncSession, current_user: CurrentUser, meeting_id: str) -> MeetingState:
    meeting = await get_facilitated_meeting(session, current_user, meeting_id)
    ended = await session.scalar(
        update(Meeting)
        .where(Meeting.id == meeting_id, ACTIVE)
        .values(ended_at=utc_now(), current_section=None, section_started_at=None)
        .returning(Meeting.id)
    )
    await session.commit()
    if ended is None:
        raise Conflict("This meeting has already ended")
    await publish_meeting(meeting.team_id, meeting_id)
    return await meeting_state(session, await load_meeting(session, meeting_id))


async def rate_meeting(session: AsyncSession, current_user: CurrentUser, meeting_id: str, rating: int) -> MeetingState:
    meeting = await get_readable_meeting(session, current_user, meeting_id)
    if current_user.role is UserRole.OBSERVER:
        raise Forbidden("Observers can follow the meeting but cannot rate it")
    meeting = await session.scalar(
        select(Meeting).where(Meeting.id == meeting_id).with_for_update().execution_options(populate_existing=True)
    )
    if not await is_attendee(session, meeting_id, current_user.id):
        raise Forbidden("Join the meeting before rating it")
    ensure_running(meeting)
    if meeting.current_section is not MeetingSection.CONCLUDE:
        raise Conflict("Ratings open in Conclude")
    now = utc_now()
    await session.execute(
        insert(MeetingRating)
        .values(meeting_id=meeting_id, user_id=current_user.id, rating=rating, rated_at=now)
        .on_conflict_do_update(
            index_elements=[MeetingRating.meeting_id, MeetingRating.user_id],
            set_={"rating": rating, "rated_at": now, "updated_at": now},
        )
    )
    await session.commit()
    await publish_meeting(meeting.team_id, meeting_id)
    return await meeting_state(session, await load_meeting(session, meeting_id))


async def is_attendee(session: AsyncSession, meeting_id: str, user_id: str) -> bool:
    attendee = await session.get(MeetingAttendee, (meeting_id, user_id))
    return attendee is not None


async def active_meeting_state(session: AsyncSession, team_id: str) -> MeetingState | None:
    active_id = await find_active_meeting_id(session, team_id)
    return await meeting_state(session, await load_meeting(session, active_id)) if active_id else None


async def publish_meeting(team_id: str, meeting_id: str) -> None:
    hub = current_hub()
    async with hub.in_order(team_id):
        async with SessionLocal() as session:
            state = await meeting_state(session, await load_meeting(session, meeting_id))
        await hub.send(team_id, meeting_message(state))


def meeting_message(state: MeetingState | None) -> dict[str, Any]:
    return {"type": "meeting", "meeting": state.model_dump(mode="json") if state else None}


async def load_meeting(session: AsyncSession, meeting_id: str) -> Meeting:
    meeting = await session.get(Meeting, meeting_id, populate_existing=True)
    if meeting is None:
        raise NotFound("Meeting not found")
    return meeting


async def get_readable_meeting(session: AsyncSession, current_user: CurrentUser, meeting_id: str) -> Meeting:
    meeting = await load_meeting(session, meeting_id)
    ensure_can_read_team(current_user, meeting.team_id, "Meeting")
    return meeting


async def get_facilitated_meeting(session: AsyncSession, current_user: CurrentUser, meeting_id: str) -> Meeting:
    meeting = await get_readable_meeting(session, current_user, meeting_id)
    if meeting.facilitator_id != current_user.id:
        raise Forbidden("Only the facilitator can move the meeting on or end it")
    ensure_running(meeting)
    return meeting


def ensure_running(meeting: Meeting) -> None:
    if meeting.ended_at is not None:
        raise Conflict("This meeting has already ended")


async def meeting_state(session: AsyncSession, meeting: Meeting) -> MeetingState:
    now = utc_now()
    facilitator = await session.get(User, meeting.facilitator_id)
    attendees = await session.scalars(
        select(User)
        .join(MeetingAttendee, MeetingAttendee.user_id == User.id)
        .where(MeetingAttendee.meeting_id == meeting.id)
        .order_by(User.name, User.id)
    )
    ratings = await session.execute(
        select(User, MeetingRating.rating)
        .join(MeetingRating, MeetingRating.user_id == User.id)
        .where(MeetingRating.meeting_id == meeting.id)
        .order_by(User.name, User.id)
    )
    timer = None
    if meeting.current_section is not None and meeting.section_started_at is not None:
        timer = section_timer(meeting.current_section, meeting.section_started_at, now)
    return MeetingState(
        id=meeting.id,
        team_id=meeting.team_id,
        facilitator=UserRef.model_validate(facilitator),
        attendees=[UserRef.model_validate(attendee) for attendee in attendees],
        ratings=[MeetingRatingOut(user=UserRef.model_validate(user), rating=rating) for user, rating in ratings],
        started_at=meeting.started_at,
        ended_at=meeting.ended_at,
        section=meeting.current_section,
        section_started_at=meeting.section_started_at,
        section_ends_at=timer.ends_at if timer else None,
        over_time=timer.over_time if timer else False,
        server_now=now,
    )
