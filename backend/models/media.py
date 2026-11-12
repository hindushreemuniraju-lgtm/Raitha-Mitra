"""Persistent uploaded media asset model (images and PDFs)."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_hex() -> str:
    return uuid.uuid4().hex


class MediaAsset(Base):
    """Stores verified uploaded images and PDFs persistently across refreshes & serverless deploys."""

    __tablename__ = "media_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_hex)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_kind: Mapped[str] = mapped_column(String(16), nullable=False, default="image")  # image | pdf
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    farmer = relationship("Farmer", back_populates="media_assets")
