"""Pest and disease image scan history."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DiseaseScan(Base):
    """Crop leaf/plant scan record per farmer."""

    __tablename__ = "disease_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), index=True)

    crop_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    media_asset_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    file_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    adapter_used: Mapped[str] = mapped_column(String(60), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # diagnosed | uncertain | not_configured
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    diagnosis_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    symptoms: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    organic_treatments: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    chemical_treatments: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    precautions: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    raw_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    farmer = relationship("Farmer", back_populates="disease_scans")
