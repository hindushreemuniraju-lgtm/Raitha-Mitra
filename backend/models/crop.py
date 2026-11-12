"""Tracked crops for growth stage monitoring."""

from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TrackedCrop(Base):
    """Crop plot actively monitored by a farmer."""

    __tablename__ = "tracked_crops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), index=True)

    crop_name: Mapped[str] = mapped_column(String(80), nullable=False)
    variety: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="cereal")
    sowing_date: Mapped[date] = mapped_column(Date, nullable=False)
    acreage: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    irrigation_type: Mapped[str] = mapped_column(String(40), nullable=False, default="rainfed")
    current_stage: Mapped[str] = mapped_column(String(60), nullable=False, default="germination")
    completed_tasks: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    photo_asset_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    farmer = relationship("Farmer", back_populates="tracked_crops")
