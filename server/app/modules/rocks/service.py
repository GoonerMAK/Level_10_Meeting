from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.calculations.rocks import rock_progress, rock_status
from app.core.permissions import CurrentUser
from app.core.schemas import UserRef
from app.models import Rock, User
from app.modules.rocks.schemas import MilestoneOut, RockList, RockOut
from app.modules.teams.service import readable_team_clock


async def list_rocks(session: AsyncSession, current_user: CurrentUser, team_id: str) -> RockList:
    clock = await readable_team_clock(session, current_user, team_id)
    rocks = await session.scalars(
        select(Rock)
        .join(User, User.id == Rock.owner_id)
        .where(Rock.team_id == team_id, Rock.quarter == clock.quarter)
        .options(selectinload(Rock.owner), selectinload(Rock.milestones))
        .order_by(User.name, Rock.title, Rock.id)
    )
    return RockList(
        quarter=clock.quarter,
        rocks=[
            RockOut(
                id=rock.id,
                title=rock.title,
                owner=UserRef.model_validate(rock.owner),
                status=rock_status(rock.status, rock.milestones, clock.today),
                progress_percent=rock_progress(rock.status, rock.milestones),
                milestones=[MilestoneOut.model_validate(milestone) for milestone in rock.milestones],
            )
            for rock in rocks
        ],
    )
