from typing import Annotated

from fastapi import Depends, Header

from app.core.errors import Unauthorized
from app.core.permissions import CurrentUser
from app.db.session import DbSession
from app.modules.auth.service import load_current_user


async def get_current_user(session: DbSession, x_user_id: Annotated[str | None, Header()] = None) -> CurrentUser:
    if not x_user_id:
        raise Unauthorized("Choose a user first")
    return await load_current_user(session, x_user_id)


SignedInUser = Annotated[CurrentUser, Depends(get_current_user)]
