"""pause the clock while the server is stopped

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-27 20:00:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = '0004'
down_revision: str | None = '0003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.rename_table('clock_starts', 'app_clocks')
    op.execute('ALTER TABLE app_clocks RENAME CONSTRAINT pk_clock_starts TO pk_app_clocks')
    op.alter_column('app_clocks', 'started_at', new_column_name='reached_at')
    op.execute('UPDATE app_clocks SET reached_at = app_now + (now() - reached_at)')


def downgrade() -> None:
    op.execute('UPDATE app_clocks SET reached_at = now() - (reached_at - app_now)')
    op.alter_column('app_clocks', 'reached_at', new_column_name='started_at')
    op.execute('ALTER TABLE app_clocks RENAME CONSTRAINT pk_app_clocks TO pk_clock_starts')
    op.rename_table('app_clocks', 'clock_starts')
