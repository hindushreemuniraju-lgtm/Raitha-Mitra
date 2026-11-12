"""Initial schema for Raitha Mitra.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "farmers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("mobile", sa.String(20), nullable=False),
        sa.Column("email", sa.String(160), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("state", sa.String(80), nullable=False),
        sa.Column("district", sa.String(80), nullable=False),
        sa.Column("village", sa.String(120), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("gps_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("farm_size_acres", sa.Float(), nullable=False, server_default="2.0"),
        sa.Column("soil_type", sa.String(80), nullable=True),
        sa.Column("main_crops", sa.JSON(), nullable=False),
        sa.Column("preferred_language", sa.String(16), nullable=False, server_default="kn-IN"),
        sa.Column("farmer_category", sa.String(40), nullable=False, server_default="small"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_farmers_id", "farmers", ["id"])
    op.create_index("ix_farmers_mobile", "farmers", ["mobile"], unique=True)
    op.create_index("ix_farmers_email", "farmers", ["email"], unique=True)

    op.create_table(
        "soil_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("dataset_name", sa.String(120), nullable=True),
        sa.Column("confidence_level", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("ph", sa.Float(), nullable=True),
        sa.Column("nitrogen_kg_ha", sa.Float(), nullable=True),
        sa.Column("phosphorus_kg_ha", sa.Float(), nullable=True),
        sa.Column("potassium_kg_ha", sa.Float(), nullable=True),
        sa.Column("organic_carbon_pct", sa.Float(), nullable=True),
        sa.Column("ec_ds_m", sa.Float(), nullable=True),
        sa.Column("sulphur_ppm", sa.Float(), nullable=True),
        sa.Column("zinc_ppm", sa.Float(), nullable=True),
        sa.Column("boron_ppm", sa.Float(), nullable=True),
        sa.Column("iron_ppm", sa.Float(), nullable=True),
        sa.Column("raw_ocr_text", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column("stored_filename", sa.String(255), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_soil_records_farmer_id", "soil_records", ["farmer_id"])

    op.create_table(
        "tracked_crops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_name", sa.String(80), nullable=False),
        sa.Column("variety", sa.String(80), nullable=True),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("sowing_date", sa.Date(), nullable=False),
        sa.Column("acreage", sa.Float(), nullable=False),
        sa.Column("irrigation_type", sa.String(40), nullable=False),
        sa.Column("current_stage", sa.String(60), nullable=False),
        sa.Column("completed_tasks", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tracked_crops_farmer_id", "tracked_crops", ["farmer_id"])

    op.create_table(
        "disease_scans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_name", sa.String(80), nullable=True),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("adapter_used", sa.String(60), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("diagnosis_name", sa.String(160), nullable=True),
        sa.Column("symptoms", sa.JSON(), nullable=False),
        sa.Column("organic_treatments", sa.JSON(), nullable=False),
        sa.Column("chemical_treatments", sa.JSON(), nullable=False),
        sa.Column("precautions", sa.JSON(), nullable=False),
        sa.Column("raw_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_disease_scans_farmer_id", "disease_scans", ["farmer_id"])

    op.create_table(
        "profit_scenarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crop_name", sa.String(80), nullable=False),
        sa.Column("farm_size_acres", sa.Float(), nullable=False),
        sa.Column("seed_cost", sa.Float(), nullable=False),
        sa.Column("fertilizer_cost", sa.Float(), nullable=False),
        sa.Column("pesticide_cost", sa.Float(), nullable=False),
        sa.Column("labour_cost", sa.Float(), nullable=False),
        sa.Column("irrigation_cost", sa.Float(), nullable=False),
        sa.Column("transport_cost", sa.Float(), nullable=False),
        sa.Column("other_cost", sa.Float(), nullable=False),
        sa.Column("expected_yield_qtl_per_acre", sa.Float(), nullable=False),
        sa.Column("expected_price_per_qtl", sa.Float(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
        sa.Column("expected_revenue", sa.Float(), nullable=False),
        sa.Column("net_profit", sa.Float(), nullable=False),
        sa.Column("margin_pct", sa.Float(), nullable=False),
        sa.Column("assumptions_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_profit_scenarios_farmer_id", "profit_scenarios", ["farmer_id"])

    op.create_table(
        "voice_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language_code", sa.String(16), nullable=False),
        sa.Column("room_name", sa.String(120), nullable=True),
        sa.Column("channel", sa.String(24), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_voice_sessions_farmer_id", "voice_sessions", ["farmer_id"])

    op.create_table(
        "voice_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("language_code", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("interrupted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("context_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_voice_messages_session_id", "voice_messages", ["session_id"])
    op.create_index("ix_voice_messages_farmer_id", "voice_messages", ["farmer_id"])


def downgrade() -> None:
    op.drop_table("voice_messages")
    op.drop_table("voice_sessions")
    op.drop_table("profit_scenarios")
    op.drop_table("disease_scans")
    op.drop_table("tracked_crops")
    op.drop_table("soil_records")
    op.drop_table("farmers")
