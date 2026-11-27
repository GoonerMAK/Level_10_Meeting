from datetime import date

from fastapi import APIRouter, Response, status

from app.core.error_docs import error_responses
from app.db.session import DbSession
from app.modules.auth.dependencies import SignedInUser
from app.modules.issues import service as issues_service
from app.modules.issues.schemas import IssueOut
from app.modules.scorecard import service
from app.modules.scorecard.schemas import Scorecard, ScoreCell, ScoreUpdate

router = APIRouter(tags=["scorecard"])


@router.get("/teams/{team_id}/scorecard", responses=error_responses(401, 404))
async def read_scorecard(team_id: str, session: DbSession, current_user: SignedInUser) -> Scorecard:
    return await service.get_scorecard(session, current_user, team_id)


@router.put("/measurables/{measurable_id}/scores/{week_start}", responses=error_responses(401, 403, 404, 422))
async def update_score(
    measurable_id: str, week_start: date, body: ScoreUpdate, session: DbSession, current_user: SignedInUser
) -> ScoreCell:
    return await service.set_score(session, current_user, measurable_id, week_start, body.value)


@router.post(
    "/measurables/{measurable_id}/scores/{week_start}/issue",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_200_OK: {"description": "An unsolved Issue for this score already exists", "model": IssueOut},
        **error_responses(401, 403, 404, 409, 422),
    },
)
async def make_issue_from_score(
    measurable_id: str, week_start: date, response: Response, session: DbSession, current_user: SignedInUser
) -> IssueOut:
    issue, created = await issues_service.create_issue_from_score(session, current_user, measurable_id, week_start)
    if not created:
        response.status_code = status.HTTP_200_OK
    return IssueOut.from_issue(issue)
