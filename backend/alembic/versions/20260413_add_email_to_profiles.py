"""Add email to profiles table

Revision ID: 20260413_add_email_to_profiles
Revises: 20260413_0001_add_skill_taxonomy
Create Date: 2026-04-13 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260413_add_email_to_profiles'
down_revision: Union[str, None] = '20260413_add_skill_taxonomy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'profiles',
        sa.Column('email', sa.String(255), nullable=True),
    )
    op.create_index(op.f('ix_profiles_email'), 'profiles', ['email'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_profiles_email'), table_name='profiles')
    op.drop_column('profiles', 'email')
