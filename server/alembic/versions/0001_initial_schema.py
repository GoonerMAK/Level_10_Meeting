"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-11-26 21:48:41.758527
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('companies',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('timezone', sa.Text(), nullable=False),
    sa.CheckConstraint('length(trim(name)) > 0', name=op.f('ck_companies_name_not_blank')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_companies'))
    )
    op.create_table('teams',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('company_id', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.CheckConstraint('length(trim(name)) > 0', name=op.f('ck_teams_name_not_blank')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_teams_company_id_companies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_teams'))
    )
    op.create_index(op.f('ix_teams_company_id'), 'teams', ['company_id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('company_id', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('email', sa.Text(), nullable=False),
    sa.Column('role', sa.Enum('admin', 'team_member', 'observer', name='user_role'), nullable=False),
    sa.CheckConstraint("email = lower(email) AND position('@' in email) > 1", name=op.f('ck_users_email_format')),
    sa.CheckConstraint('length(trim(name)) > 0', name=op.f('ck_users_name_not_blank')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_users_company_id_companies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_index(op.f('ix_users_company_id'), 'users', ['company_id'], unique=False)
    op.create_table('activity_logs',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('actor_id', sa.Text(), nullable=True),
    sa.Column('team_id', sa.Text(), nullable=True),
    sa.Column('entity', sa.Enum('score', 'issue', 'todo', 'meeting', 'meeting_rating', name='audit_entity'), nullable=False),
    sa.Column('entity_id', sa.Text(), nullable=False),
    sa.Column('entity_label', sa.Text(), nullable=False),
    sa.Column('action', sa.Enum('created', 'updated', 'deleted', 'solved', name='audit_action'), nullable=False),
    sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
    sa.CheckConstraint("jsonb_typeof(changes) = 'array'", name=op.f('ck_activity_logs_changes_is_array')),
    sa.CheckConstraint('length(trim(entity_label)) > 0', name=op.f('ck_activity_logs_entity_label_not_blank')),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_activity_logs_actor_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_activity_logs_team_id_teams'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_activity_logs'))
    )
    op.create_index('ix_activity_logs_entity', 'activity_logs', ['entity', 'entity_id'], unique=False)
    op.create_index('ix_activity_logs_team_created', 'activity_logs', ['team_id', 'created_at'], unique=False)
    op.create_table('measurables',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('team_id', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('owner_id', sa.Text(), nullable=False),
    sa.Column('unit', sa.Text(), nullable=False),
    sa.Column('goal_type', sa.Enum('at_least', 'at_most', 'between', 'exactly', name='goal_type'), nullable=False),
    sa.Column('goal_value', sa.Numeric(), nullable=True),
    sa.Column('goal_min', sa.Numeric(), nullable=True),
    sa.Column('goal_max', sa.Numeric(), nullable=True),
    sa.CheckConstraint("(goal_type = 'between' AND goal_value IS NULL AND goal_min IS NOT NULL AND goal_max IS NOT NULL AND goal_min <= goal_max) OR (goal_type <> 'between' AND goal_value IS NOT NULL AND goal_min IS NULL AND goal_max IS NULL)", name=op.f('ck_measurables_goal_shape')),
    sa.CheckConstraint('length(trim(name)) > 0', name=op.f('ck_measurables_name_not_blank')),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_measurables_owner_id_users')),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_measurables_team_id_teams')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_measurables'))
    )
    op.create_index(op.f('ix_measurables_owner_id'), 'measurables', ['owner_id'], unique=False)
    op.create_index(op.f('ix_measurables_team_id'), 'measurables', ['team_id'], unique=False)
    op.create_table('meetings',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('team_id', sa.Text(), nullable=False),
    sa.Column('facilitator_id', sa.Text(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('current_section', sa.Enum('scorecard', 'ids', 'conclude', name='meeting_section'), nullable=True),
    sa.Column('section_started_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('(ended_at IS NULL AND current_section IS NOT NULL AND section_started_at IS NOT NULL) OR (ended_at IS NOT NULL AND current_section IS NULL AND section_started_at IS NULL)', name=op.f('ck_meetings_active_has_section')),
    sa.CheckConstraint('ended_at IS NULL OR ended_at >= started_at', name=op.f('ck_meetings_ended_after_started')),
    sa.ForeignKeyConstraint(['facilitator_id'], ['users.id'], name=op.f('fk_meetings_facilitator_id_users')),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_meetings_team_id_teams')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_meetings'))
    )
    op.create_index(op.f('ix_meetings_team_id'), 'meetings', ['team_id'], unique=False)
    op.create_index('uq_meetings_one_active_per_team', 'meetings', ['team_id'], unique=True, postgresql_where=sa.text('ended_at IS NULL'))
    op.create_table('memberships',
    sa.Column('user_id', sa.Text(), nullable=False),
    sa.Column('team_id', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_memberships_team_id_teams'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_memberships_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'team_id', name=op.f('pk_memberships'))
    )
    op.create_index(op.f('ix_memberships_team_id'), 'memberships', ['team_id'], unique=False)
    op.create_table('rocks',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('team_id', sa.Text(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('owner_id', sa.Text(), nullable=False),
    sa.Column('quarter', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('on_track', 'off_track', 'complete', name='rock_status'), nullable=False),
    sa.CheckConstraint("quarter ~ '^[0-9]{4}-Q[1-4]$'", name=op.f('ck_rocks_quarter_format')),
    sa.CheckConstraint('length(trim(title)) > 0', name=op.f('ck_rocks_title_not_blank')),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_rocks_owner_id_users')),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_rocks_team_id_teams')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rocks'))
    )
    op.create_index(op.f('ix_rocks_owner_id'), 'rocks', ['owner_id'], unique=False)
    op.create_index(op.f('ix_rocks_quarter'), 'rocks', ['quarter'], unique=False)
    op.create_index(op.f('ix_rocks_team_id'), 'rocks', ['team_id'], unique=False)
    op.create_table('issues',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('team_id', sa.Text(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('owner_id', sa.Text(), nullable=False),
    sa.Column('priority', sa.SmallInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('solved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolution_note', sa.Text(), nullable=True),
    sa.Column('source_measurable_id', sa.Text(), nullable=True),
    sa.Column('source_week_start', sa.Date(), nullable=True),
    sa.CheckConstraint('(solved_at IS NULL AND resolution_note IS NULL) OR (solved_at IS NOT NULL AND resolution_note IS NOT NULL AND length(trim(resolution_note)) > 0)', name=op.f('ck_issues_solved_requires_note')),
    sa.CheckConstraint('(source_measurable_id IS NULL) = (source_week_start IS NULL)', name=op.f('ck_issues_source_complete')),
    sa.CheckConstraint('length(trim(title)) > 0', name=op.f('ck_issues_title_not_blank')),
    sa.CheckConstraint('priority BETWEEN 1 AND 5', name=op.f('ck_issues_priority_range')),
    sa.CheckConstraint('solved_at IS NULL OR solved_at >= created_at', name=op.f('ck_issues_solved_after_created')),
    sa.CheckConstraint('source_week_start IS NULL OR extract(isodow from source_week_start) = 1', name=op.f('ck_issues_source_week_is_monday')),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_issues_owner_id_users')),
    sa.ForeignKeyConstraint(['source_measurable_id'], ['measurables.id'], name=op.f('fk_issues_source_measurable_id_measurables')),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_issues_team_id_teams')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_issues'))
    )
    op.create_index(op.f('ix_issues_owner_id'), 'issues', ['owner_id'], unique=False)
    op.create_index(op.f('ix_issues_team_id'), 'issues', ['team_id'], unique=False)
    op.create_index('ix_issues_team_open', 'issues', ['team_id'], unique=False, postgresql_where=sa.text('solved_at IS NULL'))
    op.create_index('uq_issues_open_source', 'issues', ['source_measurable_id', 'source_week_start'], unique=True, postgresql_where=sa.text('solved_at IS NULL AND source_measurable_id IS NOT NULL'))
    op.create_table('meeting_attendees',
    sa.Column('meeting_id', sa.Text(), nullable=False),
    sa.Column('user_id', sa.Text(), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], name=op.f('fk_meeting_attendees_meeting_id_meetings'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_meeting_attendees_user_id_users')),
    sa.PrimaryKeyConstraint('meeting_id', 'user_id', name=op.f('pk_meeting_attendees'))
    )
    op.create_table('milestones',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('rock_id', sa.Text(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('done', sa.Boolean(), server_default='false', nullable=False),
    sa.CheckConstraint('length(trim(title)) > 0', name=op.f('ck_milestones_title_not_blank')),
    sa.ForeignKeyConstraint(['rock_id'], ['rocks.id'], name=op.f('fk_milestones_rock_id_rocks'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_milestones'))
    )
    op.create_index(op.f('ix_milestones_rock_id'), 'milestones', ['rock_id'], unique=False)
    op.create_table('scores',
    sa.Column('measurable_id', sa.Text(), nullable=False),
    sa.Column('week_start', sa.Date(), nullable=False),
    sa.Column('value', sa.Numeric(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_by_id', sa.Text(), nullable=True),
    sa.CheckConstraint('extract(isodow from week_start) = 1', name=op.f('ck_scores_week_start_is_monday')),
    sa.ForeignKeyConstraint(['measurable_id'], ['measurables.id'], name=op.f('fk_scores_measurable_id_measurables'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], name=op.f('fk_scores_updated_by_id_users')),
    sa.PrimaryKeyConstraint('measurable_id', 'week_start', name=op.f('pk_scores'))
    )
    op.create_table('meeting_ratings',
    sa.Column('meeting_id', sa.Text(), nullable=False),
    sa.Column('user_id', sa.Text(), nullable=False),
    sa.Column('rating', sa.SmallInteger(), nullable=False),
    sa.Column('rated_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('rating BETWEEN 1 AND 10', name=op.f('ck_meeting_ratings_rating_range')),
    sa.ForeignKeyConstraint(['meeting_id', 'user_id'], ['meeting_attendees.meeting_id', 'meeting_attendees.user_id'], name='fk_meeting_ratings_attendee', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('meeting_id', 'user_id', name=op.f('pk_meeting_ratings'))
    )
    op.create_table('todos',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('team_id', sa.Text(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('owner_id', sa.Text(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('done_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('source_issue_id', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('length(trim(title)) > 0', name=op.f('ck_todos_title_not_blank')),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_todos_owner_id_users')),
    sa.ForeignKeyConstraint(['source_issue_id'], ['issues.id'], name=op.f('fk_todos_source_issue_id_issues'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_todos_team_id_teams')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_todos'))
    )
    op.create_index(op.f('ix_todos_due_date'), 'todos', ['due_date'], unique=False)
    op.create_index(op.f('ix_todos_owner_id'), 'todos', ['owner_id'], unique=False)
    op.create_index(op.f('ix_todos_source_issue_id'), 'todos', ['source_issue_id'], unique=False)
    op.create_index(op.f('ix_todos_team_id'), 'todos', ['team_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_todos_team_id'), table_name='todos')
    op.drop_index(op.f('ix_todos_source_issue_id'), table_name='todos')
    op.drop_index(op.f('ix_todos_owner_id'), table_name='todos')
    op.drop_index(op.f('ix_todos_due_date'), table_name='todos')
    op.drop_table('todos')
    op.drop_table('meeting_ratings')
    op.drop_table('scores')
    op.drop_index(op.f('ix_milestones_rock_id'), table_name='milestones')
    op.drop_table('milestones')
    op.drop_table('meeting_attendees')
    op.drop_index('uq_issues_open_source', table_name='issues', postgresql_where=sa.text('solved_at IS NULL AND source_measurable_id IS NOT NULL'))
    op.drop_index('ix_issues_team_open', table_name='issues', postgresql_where=sa.text('solved_at IS NULL'))
    op.drop_index(op.f('ix_issues_team_id'), table_name='issues')
    op.drop_index(op.f('ix_issues_owner_id'), table_name='issues')
    op.drop_table('issues')
    op.drop_index(op.f('ix_rocks_team_id'), table_name='rocks')
    op.drop_index(op.f('ix_rocks_quarter'), table_name='rocks')
    op.drop_index(op.f('ix_rocks_owner_id'), table_name='rocks')
    op.drop_table('rocks')
    op.drop_index(op.f('ix_memberships_team_id'), table_name='memberships')
    op.drop_table('memberships')
    op.drop_index('uq_meetings_one_active_per_team', table_name='meetings', postgresql_where=sa.text('ended_at IS NULL'))
    op.drop_index(op.f('ix_meetings_team_id'), table_name='meetings')
    op.drop_table('meetings')
    op.drop_index(op.f('ix_measurables_team_id'), table_name='measurables')
    op.drop_index(op.f('ix_measurables_owner_id'), table_name='measurables')
    op.drop_table('measurables')
    op.drop_index('ix_activity_logs_team_created', table_name='activity_logs')
    op.drop_index('ix_activity_logs_entity', table_name='activity_logs')
    op.drop_table('activity_logs')
    op.drop_index(op.f('ix_users_company_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_teams_company_id'), table_name='teams')
    op.drop_table('teams')
    op.drop_table('companies')
    for enum_name in ("audit_action", "audit_entity", "meeting_section", "rock_status", "goal_type", "user_role"):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
