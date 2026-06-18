"""create initial smartdrain tables

Revision ID: 20260618_0001
Revises:
Create Date: 2026-06-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260618_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "drains",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drain_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_drains_drain_code"), "drains", ["drain_code"], unique=True)
    op.create_index(op.f("ix_drains_id"), "drains", ["id"], unique=False)
    op.create_index(op.f("ix_drains_status"), "drains", ["status"], unique=False)

    op.create_table(
        "sensor_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drain_id", sa.Integer(), nullable=False),
        sa.Column("water_level_cm", sa.Float(), nullable=False),
        sa.Column("flow_velocity_mps", sa.Float(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["drain_id"], ["drains.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sensor_data_drain_id"), "sensor_data", ["drain_id"], unique=False)
    op.create_index(op.f("ix_sensor_data_id"), "sensor_data", ["id"], unique=False)

    op.create_table(
        "yolo_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drain_id", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("obstruction_ratio", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("yolo_status", sa.String(length=20), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["drain_id"], ["drains.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_yolo_results_drain_id"), "yolo_results", ["drain_id"], unique=False)
    op.create_index(op.f("ix_yolo_results_id"), "yolo_results", ["id"], unique=False)

    op.create_table(
        "xgboost_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drain_id", sa.Integer(), nullable=False),
        sa.Column("sensor_data_id", sa.Integer(), nullable=True),
        sa.Column("yolo_result_id", sa.Integer(), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("final_decision", sa.String(length=255), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["drain_id"], ["drains.id"]),
        sa.ForeignKeyConstraint(["sensor_data_id"], ["sensor_data.id"]),
        sa.ForeignKeyConstraint(["yolo_result_id"], ["yolo_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_xgboost_results_drain_id"), "xgboost_results", ["drain_id"], unique=False)
    op.create_index(op.f("ix_xgboost_results_id"), "xgboost_results", ["id"], unique=False)
    op.create_index(op.f("ix_xgboost_results_risk_level"), "xgboost_results", ["risk_level"], unique=False)
    op.create_index(op.f("ix_xgboost_results_sensor_data_id"), "xgboost_results", ["sensor_data_id"], unique=False)
    op.create_index(op.f("ix_xgboost_results_yolo_result_id"), "xgboost_results", ["yolo_result_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_xgboost_results_yolo_result_id"), table_name="xgboost_results")
    op.drop_index(op.f("ix_xgboost_results_sensor_data_id"), table_name="xgboost_results")
    op.drop_index(op.f("ix_xgboost_results_risk_level"), table_name="xgboost_results")
    op.drop_index(op.f("ix_xgboost_results_id"), table_name="xgboost_results")
    op.drop_index(op.f("ix_xgboost_results_drain_id"), table_name="xgboost_results")
    op.drop_table("xgboost_results")

    op.drop_index(op.f("ix_yolo_results_id"), table_name="yolo_results")
    op.drop_index(op.f("ix_yolo_results_drain_id"), table_name="yolo_results")
    op.drop_table("yolo_results")

    op.drop_index(op.f("ix_sensor_data_id"), table_name="sensor_data")
    op.drop_index(op.f("ix_sensor_data_drain_id"), table_name="sensor_data")
    op.drop_table("sensor_data")

    op.drop_index(op.f("ix_drains_status"), table_name="drains")
    op.drop_index(op.f("ix_drains_id"), table_name="drains")
    op.drop_index(op.f("ix_drains_drain_code"), table_name="drains")
    op.drop_table("drains")
