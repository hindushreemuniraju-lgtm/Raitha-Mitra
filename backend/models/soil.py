"""Soil health records (lab reports, Soil Health Cards, and dataset estimates)."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SoilRecord(Base):
    """Per-farmer soil test or clearly labelled dataset estimate."""

    __tablename__ = "soil_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), index=True)

    # lab_report | soil_health_card | dataset_estimate
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    dataset_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(24), nullable=False, default="high")
    # pending_review | verified
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending_review")

    ph: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nitrogen_kg_ha: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    phosphorus_kg_ha: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    potassium_kg_ha: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    organic_carbon_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ec_ds_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sulphur_ppm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    zinc_ppm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    boron_ppm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iron_ppm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    raw_ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stored_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    farmer = relationship("Farmer", back_populates="soil_records")
