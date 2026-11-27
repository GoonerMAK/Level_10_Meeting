from fastapi import APIRouter, Response, status

from app.core.error_docs import error_responses
from app.db.session import DbSession
from app.modules.auth.dependencies import SignedInUser
from app.modules.meetings import service
from app.modules.meetings.schemas import MeetingState, MeetingSummary, NextSection, RatingUpdate

router = APIRouter(tags=["meetings"])


@router.post(
    "/teams/{team_id}/meetings",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_200_OK: {"description": "The team's running meeting, now joined", "model": MeetingState},
        **error_responses(401, 403, 404, 409),
    },
)
async def start_meeting(team_id: str, response: Response, session: DbSession, current_user: SignedInUser) -> MeetingState:
    meeting, created = await service.start_meeting(session, current_user, team_id)
    if not created:
        response.status_code = status.HTTP_200_OK
    return meeting


@router.get("/teams/{team_id}/meetings/active", responses=error_responses(401, 404))
async def read_active_meeting(team_id: str, session: DbSession, current_user: SignedInUser) -> MeetingState:
    return await service.get_active_meeting(session, current_user, team_id)


@router.get("/meetings/{meeting_id}", responses=error_responses(401, 404))
async def read_meeting(meeting_id: str, session: DbSession, current_user: SignedInUser) -> MeetingState:
    return await service.get_meeting(session, current_user, meeting_id)


@router.get("/meetings/{meeting_id}/summary", responses=error_responses(401, 404, 409))
async def read_meeting_summary(meeting_id: str, session: DbSession, current_user: SignedInUser) -> MeetingSummary:
    return await service.get_meeting_summary(session, current_user, meeting_id)


@router.post("/meetings/{meeting_id}/join", responses=error_responses(401, 404, 409))
async def join_meeting(meeting_id: str, session: DbSession, current_user: SignedInUser) -> MeetingState:
    return await service.join_meeting(session, current_user, meeting_id)


@router.post("/meetings/{meeting_id}/next", responses=error_responses(401, 403, 404, 409, 422))
async def move_to_next_section(
    meeting_id: str, body: NextSection, session: DbSession, current_user: SignedInUser
) -> MeetingState:
    return await service.move_to_next_section(session, current_user, meeting_id, body.from_section)


@router.post("/meetings/{meeting_id}/end", responses=error_responses(401, 403, 404, 409))
async def end_meeting(meeting_id: str, session: DbSession, current_user: SignedInUser) -> MeetingState:
    return await service.end_meeting(session, current_user, meeting_id)


@router.put("/meetings/{meeting_id}/rating", responses=error_responses(401, 403, 404, 409, 422))
async def rate_meeting(meeting_id: str, body: RatingUpdate, session: DbSession, current_user: SignedInUser) -> MeetingState:
    return await service.rate_meeting(session, current_user, meeting_id, body.rating)
