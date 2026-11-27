"""add clock_starts so the clock survives restarts

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-27 18:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0003'
down_revision: str | None = '0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'clock_starts',
        sa.Column('app_now', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('app_now', name=op.f('pk_clock_starts')),
    )


def downgrade() -> None:
    op.drop_table('clock_starts')
