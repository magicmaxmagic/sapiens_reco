"""initial schema

Revision ID: 20260330_0001
Revises:
Create Date: 2026-03-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260330_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    default_timestamp = sa.text("CURRENT_TIMESTAMP")

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_skills", sa.JSON(), nullable=False),
        sa.Column("parsed_languages", sa.JSON(), nullable=False),
        sa.Column("parsed_location", sa.String(length=255), nullable=True),
        sa.Column("parsed_seniority", sa.String(length=100), nullable=True),
        sa.Column("availability_status", sa.String(length=100), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=default_timestamp,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=default_timestamp,
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profiles_id", "profiles", ["id"], unique=False)

    op.create_table(
        "missions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("required_language", sa.String(length=100), nullable=True),
        sa.Column("required_location", sa.String(length=255), nullable=True),
        sa.Column("required_seniority", sa.String(length=100), nullable=True),
        sa.Column("desired_start_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=default_timestamp,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=default_timestamp,
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_missions_id", "missions", ["id"], unique=False)

    op.create_table(
        "experiences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_experiences_id", "experiences", ["id"], unique=False)

    op.create_table(
        "match_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mission_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("structured_score", sa.Float(), nullable=False),
        sa.Column("semantic_score", sa.Float(), nullable=False),
        sa.Column("business_score", sa.Float(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("explanation_tags", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=default_timestamp,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=default_timestamp,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mission_id", "profile_id", name="uq_mission_profile"),
    )
    op.create_index("ix_match_results_id", "match_results", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_match_results_id", table_name="match_results")
    op.drop_table("match_results")

    op.drop_index("ix_experiences_id", table_name="experiences")
    op.drop_table("experiences")

    op.drop_index("ix_missions_id", table_name="missions")
    op.drop_table("missions")

    op.drop_index("ix_profiles_id", table_name="profiles")
    op.drop_table("profiles")
