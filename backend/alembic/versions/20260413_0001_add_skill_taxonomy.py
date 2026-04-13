"""Add skill_taxonomy table

Revision ID: 20260413_add_skill_taxonomy
Revises: 
Create Date: 2026-04-13 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260413_add_skill_taxonomy'
down_revision: Union[str, None] = '20260403_0001_add_users_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'skill_taxonomy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('synonyms', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_skill_taxonomy_id'), 'skill_taxonomy', ['id'], unique=False)
    op.create_index(op.f('ix_skill_taxonomy_name'), 'skill_taxonomy', ['name'], unique=True)
    op.create_index(op.f('ix_skill_taxonomy_category'), 'skill_taxonomy', ['category'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_skill_taxonomy_category'), table_name='skill_taxonomy')
    op.drop_index(op.f('ix_skill_taxonomy_name'), table_name='skill_taxonomy')
    op.drop_index(op.f('ix_skill_taxonomy_id'), table_name='skill_taxonomy')
    op.drop_table('skill_taxonomy')
