"""create analysis jobs table

Revision ID: 20260619_0002
Revises: 20260618_0001
Create Date: 2026-06-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260619_0002"
down_revision: str | None = "20260618_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=80), nullable=False),
        sa.Column("job_id", sa.String(length=80), nullable=True),
        sa.Column("drain_id", sa.Integer(), nullable=False),
        sa.Column("sensor_data_id", sa.Integer(), nullable=False),
        sa.Column("sensor_measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("yolo_result_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["drain_id"], ["drains.id"]),
        sa.ForeignKeyConstraint(["sensor_data_id"], ["sensor_data.id"]),
        sa.ForeignKeyConstraint(["yolo_result_id"], ["yolo_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_jobs_drain_id"), "analysis_jobs", ["drain_id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_id"), "analysis_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_job_id"), "analysis_jobs", ["job_id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_request_id"), "analysis_jobs", ["request_id"], unique=True)
    op.create_index(op.f("ix_analysis_jobs_sensor_data_id"), "analysis_jobs", ["sensor_data_id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_status"), "analysis_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_yolo_result_id"), "analysis_jobs", ["yolo_result_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_jobs_yolo_result_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_status"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_sensor_data_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_request_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_job_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_drain_id"), table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
