"""Add users, sessions, and audit_logs tables.

Revision ID: 20260403_0001
Revises: 20260330_0001
Create Date: 2026-04-03

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260403_0001'
down_revision: str | None = '20260330_0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False,
                  server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False,
                  server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('reset_token', sa.String(255), nullable=True),
        sa.Column('reset_token_expires', sa.DateTime(), nullable=True),
        sa.Column('totp_secret', sa.String(32), nullable=True),
        sa.Column('totp_enabled', sa.Boolean(), nullable=False,
                  server_default='false'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('refresh_token_hash', sa.String(64), nullable=False),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False,
                  server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
        sa.UniqueConstraint('refresh_token_hash'),
    )
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.UUID(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    # Add new columns to existing tables
    # Profiles table
    op.add_column('profiles', sa.Column('created_by', sa.UUID(), nullable=True))
    op.add_column('profiles', sa.Column('updated_by', sa.UUID(), nullable=True))
    op.add_column('profiles', sa.Column('is_active', sa.Boolean(),
                                        nullable=False, server_default='true'))
    op.add_column('profiles', sa.Column('tags', sa.JSON(),
                                        nullable=False, server_default='[]'))

    # Missions table
    op.add_column('missions', sa.Column('status', sa.String(50),
                                        nullable=False, server_default='draft'))
    op.add_column('missions', sa.Column('priority', sa.String(50),
                                       nullable=False, server_default='medium'))
    op.add_column('missions', sa.Column('created_by', sa.UUID(), nullable=True))
    op.add_column('missions', sa.Column('is_active', sa.Boolean(),
                                        nullable=False, server_default='true'))

    # Create indexes on new columns
    op.create_index('ix_profiles_created_by', 'profiles', ['created_by'],
                    unique=False)
    op.create_index('ix_missions_created_by', 'missions', ['created_by'],
                    unique=False)
    op.create_index('ix_missions_status', 'missions', ['status'], unique=False)

    # Add feedback columns to match_results
    op.add_column('match_results', sa.Column('feedback', sa.String(20),
                                             nullable=True))
    op.add_column('match_results', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('match_results', sa.Column('feedback_by', sa.UUID(),
                                             nullable=True))
    op.add_column('match_results', sa.Column('feedback_at', sa.DateTime(),
                                             nullable=True))
    op.create_foreign_key('fk_match_results_feedback_by', 'match_results',
                          'users', ['feedback_by'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Drop foreign key first
    op.drop_constraint('fk_match_results_feedback_by', 'match_results',
                       type_='foreignkey')

    # Drop columns from match_results
    op.drop_column('match_results', 'feedback_at')
    op.drop_column('match_results', 'feedback_by')
    op.drop_column('match_results', 'notes')
    op.drop_column('match_results', 'feedback')

    # Drop indexes
    op.drop_index('ix_missions_status', 'missions')
    op.drop_index('ix_missions_created_by', 'missions')
    op.drop_index('ix_profiles_created_by', 'profiles')

    # Drop columns from missions
    op.drop_column('missions', 'is_active')
    op.drop_column('missions', 'created_by')
    op.drop_column('missions', 'priority')
    op.drop_column('missions', 'status')

    # Drop columns from profiles
    op.drop_column('profiles', 'tags')
    op.drop_column('profiles', 'is_active')
    op.drop_column('profiles', 'updated_by')
    op.drop_column('profiles', 'created_by')

    # Drop tables
    op.drop_index('ix_audit_logs_created_at', 'audit_logs')
    op.drop_index('ix_audit_logs_action', 'audit_logs')
    op.drop_index('ix_audit_logs_user_id', 'audit_logs')
    op.drop_table('audit_logs')

    op.drop_index('ix_sessions_user_id', 'sessions')
    op.drop_table('sessions')

    op.drop_index('ix_users_email', 'users')
    op.drop_table('users')