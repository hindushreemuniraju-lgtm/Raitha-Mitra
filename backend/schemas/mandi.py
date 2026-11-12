"""Mandi prices schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MandiPriceRowOut(BaseModel):
    state: str
    district: str
    market: str
    commodity: str
    variety: str
    min_price_inr: float
    max_price_inr: float
    modal_price_inr: float
    arrivals_tonnes: Optional[float] = None
    price_date: str
    source: str


class MandiResponseOut(BaseModel):
    label: str
    is_demo_data: bool
    source_statuses: Dict[str, Dict[str, str]]
    updated_at: Optional[str] = None
    records: List[MandiPriceRowOut]
    history_series: List[Dict[str, Any]]
    market_comparison: List[Dict[str, Any]]
