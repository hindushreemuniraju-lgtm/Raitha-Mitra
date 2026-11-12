"""Saved profit calculator scenarios."""

from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProfitScenario(Base):
    """Editable farm economics calculation saved by a farmer."""

    __tablename__ = "profit_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), index=True)

    crop_name: Mapped[str] = mapped_column(String(80), nullable=False)
    farm_size_acres: Mapped[float] = mapped_column(Float, nullable=False)
    seed_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fertilizer_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pesticide_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    labour_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    irrigation_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    transport_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    other_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    expected_yield_qtl_per_acre: Mapped[float] = mapped_column(Float, nullable=False)
    expected_price_per_qtl: Mapped[float] = mapped_column(Float, nullable=False)

    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    net_profit: Mapped[float] = mapped_column(Float, nullable=False)
    margin_pct: Mapped[float] = mapped_column(Float, nullable=False)
    assumptions_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    farmer = relationship("Farmer", back_populates="profit_scenarios")
