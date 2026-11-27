from typing import Annotated

from fastapi import Depends, Request

from app.core.errors import Unauthorized
from app.core.permissions import CurrentUser
from app.db.session import DbSession
from app.modules.auth.service import SIGNED_IN_USER_KEY, find_current_user


async def get_current_user(request: Request, session: DbSession) -> CurrentUser:
    current_user = await find_current_user(session, request.session.get(SIGNED_IN_USER_KEY))
    if current_user is None:
        request.session.clear()
        raise Unauthorized("Choose a user first")
    return current_user


SignedInUser = Annotated[CurrentUser, Depends(get_current_user)]
