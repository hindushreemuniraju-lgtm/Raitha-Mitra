"""Smart notifications and scheduled weather monitoring logs."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Notification(Base):
    """Persistent, deduplicated agricultural & weather alert notification per farmer."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    crop_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tracked_crops.id", ondelete="SET NULL"), nullable=True, index=True)

    category: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    alert_type_label: Mapped[str] = mapped_column(String(64), nullable=False, default="general_weather_advisory")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")  # critical | high | medium | low
    dedup_key: Mapped[str] = mapped_column(String(180), nullable=False, index=True)

    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    title_kn: Mapped[str] = mapped_column(String(240), nullable=False)
    message_en: Mapped[str] = mapped_column(Text, nullable=False)
    message_kn: Mapped[str] = mapped_column(Text, nullable=False)

    crop_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    growth_stage: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    recommendation_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation_kn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False, default="Weather & Crop Engine")
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    farmer = relationship("Farmer", back_populates="notifications")


class MonitoringRunLog(Base):
    """Audit trail of scheduled backend weather & harvest monitoring runs."""

    __tablename__ = "monitoring_run_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trigger: Mapped[str] = mapped_column(String(40), nullable=False, default="scheduler")
    farmers_checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notifications_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ran_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
