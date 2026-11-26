from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Identity, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utc_now
from app.db.base import Base
from app.models.columns import UtcTimestamp, not_blank, pg_enum
from app.models.enums import AuditAction, AuditEntity


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UtcTimestamp, default=utc_now)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"))
    entity: Mapped[AuditEntity] = mapped_column(pg_enum(AuditEntity, "audit_entity"))
    entity_id: Mapped[str] = mapped_column(Text)
    entity_label: Mapped[str] = mapped_column(Text)
    action: Mapped[AuditAction] = mapped_column(pg_enum(AuditAction, "audit_action"))
    changes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))

    __table_args__ = (
        not_blank("entity_label"),
        CheckConstraint("jsonb_typeof(changes) = 'array'", name="changes_is_array"),
        Index("ix_activity_logs_entity", "entity", "entity_id"),
        Index("ix_activity_logs_team_created", "team_id", "created_at"),
    )
