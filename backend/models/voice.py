"""Voice assistant conversation sessions and messages."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class VoiceSession(Base):
    """Multilingual voice/chat session belonging to a single farmer."""

    __tablename__ = "voice_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False, default="kn-IN")
    room_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    channel: Mapped[str] = mapped_column(String(24), nullable=False, default="livekit")
    title: Mapped[str] = mapped_column(String(160), nullable=False, default="Farming Consultation")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    farmer = relationship("Farmer", back_populates="voice_sessions")
    messages = relationship("VoiceMessage", back_populates="session", cascade="all, delete-orphan")


class VoiceMessage(Base):
    """Individual utterance and grounded assistant response."""

    __tablename__ = "voice_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("voice_sessions.id", ondelete="CASCADE"), index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), index=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # farmer | assistant
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    interrupted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    context_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session = relationship("VoiceSession", back_populates="messages")
