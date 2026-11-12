"""Yield and harvest prediction schemas."""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class YieldPredictRequest(BaseModel):
    crop_name: str = Field(min_length=2, max_length=80)
    sowing_date: date
    acreage: float = Field(default=1.0, gt=0.0, le=5000.0)
    irrigation_type: str = Field(default="drip", max_length=40)
    growth_stage: str = Field(default="vegetative", max_length=40)
    pest_status: str = Field(default="none", max_length=40)
    rainfall_adequacy: str = Field(default="normal", max_length=32)


class YieldPredictOut(BaseModel):
    crop_name: str
    acreage: float
    yield_min_qtl_total: float
    yield_expected_qtl_total: float
    yield_max_qtl_total: float
    yield_per_acre_range_qtl: str
    confidence_pct: int
    confidence_label: str
    harvest_window_start: str
    harvest_window_end: str
    maturity_basis: List[str]
    risk_factors: List[str]
    google_agri_status: str
    google_agri_note: str
    google_landscape_metadata: Optional[Dict[str, Any]] = None
