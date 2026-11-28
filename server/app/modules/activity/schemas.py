from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.schemas import UserRef
from app.models.enums import AuditAction, AuditEntity


class Change(BaseModel):
    field: str
    before: Any
    after: Any


class ActivityOut(BaseModel):
    id: int
    created_at: datetime
    user: UserRef | None
    entity: AuditEntity
    entity_id: str
    entity_label: str
    action: AuditAction
    changes: list[Change]
