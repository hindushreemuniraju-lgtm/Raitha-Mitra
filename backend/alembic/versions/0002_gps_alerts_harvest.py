"""Add live GPS metadata, persistent media assets, crop photos, notifications & monitoring logs.

Revision ID: 0002_gps_alerts_harvest
Revises: 0001_initial
Create Date: 2026-11-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_gps_alerts_harvest"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("farmers", sa.Column("taluk", sa.String(80), nullable=False, server_default=""))
    op.add_column("farmers", sa.Column("location_address", sa.String(400), nullable=True))
    op.add_column("farmers", sa.Column("location_source", sa.String(24), nullable=False, server_default="manual"))
    op.add_column("farmers", sa.Column("continuous_gps_opt_in", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("farmers", sa.Column("location_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("farmers", sa.Column("avatar_asset_id", sa.String(36), nullable=True))

    op.add_column("soil_records", sa.Column("media_asset_id", sa.String(36), nullable=True))
    op.add_column("soil_records", sa.Column("file_mime_type", sa.String(100), nullable=True))

    op.add_column("disease_scans", sa.Column("original_filename", sa.String(255), nullable=True))
    op.add_column("disease_scans", sa.Column("media_asset_id", sa.String(36), nullable=True))
    op.add_column("disease_scans", sa.Column("file_mime_type", sa.String(100), nullable=True))

    op.add_column("tracked_crops", sa.Column("photo_asset_ids", sa.JSON(), nullable=False, server_default="[]"))

    op.create_table(
        "media_assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_kind", sa.String(16), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_media_assets_farmer_id", "media_assets", ["farmer_id"])
    op.create_index("ix_media_assets_category", "media_assets", ["category"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_id", sa.Integer(), sa.ForeignKey("tracked_crops.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(48), nullable=False),
        sa.Column("alert_type_label", sa.String(64), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("dedup_key", sa.String(180), nullable=False),
        sa.Column("title_en", sa.String(200), nullable=False),
        sa.Column("title_kn", sa.String(240), nullable=False),
        sa.Column("message_en", sa.Text(), nullable=False),
        sa.Column("message_kn", sa.Text(), nullable=False),
        sa.Column("crop_name", sa.String(80), nullable=True),
        sa.Column("growth_stage", sa.String(60), nullable=True),
        sa.Column("recommendation_en", sa.Text(), nullable=True),
        sa.Column("recommendation_kn", sa.Text(), nullable=True),
        sa.Column("source_name", sa.String(120), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_farmer_id", "notifications", ["farmer_id"])
    op.create_index("ix_notifications_dedup_key", "notifications", ["dedup_key"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])

    op.create_table(
        "monitoring_run_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trigger", sa.String(40), nullable=False),
        sa.Column("farmers_checked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notifications_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("ran_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_monitoring_run_logs_ran_at", "monitoring_run_logs", ["ran_at"])


def downgrade() -> None:
    op.drop_table("monitoring_run_logs")
    op.drop_table("notifications")
    op.drop_table("media_assets")
    with op.batch_alter_table("tracked_crops") as batch_op:
        batch_op.drop_column("photo_asset_ids")
    with op.batch_alter_table("disease_scans") as batch_op:
        batch_op.drop_column("file_mime_type")
        batch_op.drop_column("media_asset_id")
        batch_op.drop_column("original_filename")
    with op.batch_alter_table("soil_records") as batch_op:
        batch_op.drop_column("file_mime_type")
        batch_op.drop_column("media_asset_id")
    with op.batch_alter_table("farmers") as batch_op:
        batch_op.drop_column("avatar_asset_id")
        batch_op.drop_column("location_updated_at")
        batch_op.drop_column("continuous_gps_opt_in")
        batch_op.drop_column("location_source")
        batch_op.drop_column("location_address")
        batch_op.drop_column("taluk")
