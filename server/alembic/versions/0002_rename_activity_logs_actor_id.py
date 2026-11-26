"""rename activity_logs actor_id to user_id

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-27 12:00:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = '0002'
down_revision: str | None = '0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column('activity_logs', 'actor_id', new_column_name='user_id')
    op.execute('ALTER TABLE activity_logs RENAME CONSTRAINT fk_activity_logs_actor_id_users TO fk_activity_logs_user_id_users')


def downgrade() -> None:
    op.execute('ALTER TABLE activity_logs RENAME CONSTRAINT fk_activity_logs_user_id_users TO fk_activity_logs_actor_id_users')
    op.alter_column('activity_logs', 'user_id', new_column_name='actor_id')
