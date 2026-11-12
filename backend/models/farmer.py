"""Farmer ORM model."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Farmer(Base):
    """Registered farmer profile and preferences."""

    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    mobile: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(160), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    state: Mapped[str] = mapped_column(String(80), nullable=False, default="Karnataka")
    district: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    taluk: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    village: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    location_address: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    location_source: Mapped[str] = mapped_column(String(24), nullable=False, default="manual")
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gps_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    continuous_gps_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar_asset_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    farm_size_acres: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    soil_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    main_crops: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    preferred_language: Mapped[str] = mapped_column(String(16), nullable=False, default="kn-IN")
    farmer_category: Mapped[str] = mapped_column(String(40), nullable=False, default="small")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    soil_records = relationship("SoilRecord", back_populates="farmer", cascade="all, delete-orphan")
    tracked_crops = relationship("TrackedCrop", back_populates="farmer", cascade="all, delete-orphan")
    disease_scans = relationship("DiseaseScan", back_populates="farmer", cascade="all, delete-orphan")
    profit_scenarios = relationship("ProfitScenario", back_populates="farmer", cascade="all, delete-orphan")
    voice_sessions = relationship("VoiceSession", back_populates="farmer", cascade="all, delete-orphan")
    media_assets = relationship("MediaAsset", back_populates="farmer", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="farmer", cascade="all, delete-orphan")
