"""add_username_to_users

Revision ID: 38344406fc89
Revises: 20260403_0001
Create Date: 2026-04-13 08:10:02.019542
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38344406fc89'
down_revision: Union[str, None] = '20260403_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('username', sa.String(50), nullable=False),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_username', 'users')
    op.drop_column('users', 'username')
