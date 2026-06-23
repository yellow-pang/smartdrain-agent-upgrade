"""add trigger type to analysis jobs

Revision ID: 20260623_0003
Revises: 20260619_0002
Create Date: 2026-06-23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260623_0003"
down_revision: str | None = "20260619_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analysis_jobs",
        sa.Column("trigger_type", sa.String(length=20), nullable=False, server_default="manual"),
    )
    op.create_index(op.f("ix_analysis_jobs_trigger_type"), "analysis_jobs", ["trigger_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_jobs_trigger_type"), table_name="analysis_jobs")
    op.drop_column("analysis_jobs", "trigger_type")
