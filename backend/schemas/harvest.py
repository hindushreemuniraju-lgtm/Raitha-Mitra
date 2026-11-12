"""Crop-specific harvest protection & profit optimization schemas."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class HarvestAnalyzeRequest(BaseModel):
    crop_name: str = Field(min_length=2, max_length=80)
    variety: Optional[str] = Field(default=None, max_length=80)
    sowing_date: date
    current_stage: str = Field(default="vegetative", max_length=60)
    acreage: float = Field(default=1.0, gt=0.0, le=5000.0)
    irrigation_type: str = Field(default="drip", max_length=40)


class HarvestProfitOptimizationOut(BaseModel):
    market_price_status: str  # configured | not_configured
    current_modal_price_inr_qtl: Optional[float] = None
    market_name: Optional[str] = None
    price_date: Optional[str] = None
    spoilage_risk_level: str  # low | moderate | high
    recommended_sell_strategy: str
    transport_timing_advice: str
    explanation_en: str
    explanation_kn: str
    honesty_note: str


class HarvestProtectionItemOut(BaseModel):
    crop_id: Optional[int] = None
    crop_name: str
    variety: Optional[str] = None
    sowing_date: str
    crop_age_days: int
    current_stage: str
    expected_maturity_date: str
    days_remaining_to_maturity: int
    readiness_status: str  # immature | approaching_maturity | harvest_ready | overdue
    action: str  # harvest_now | prepare_harvest | wait_for_maturity | delay_harvest | protect_crop
    action_label_en: str
    action_label_kn: str
    rain_24h_mm: float
    rain_72h_mm: float
    max_rain_probability_pct: float
    max_wind_kmh: float
    location_label: str
    headline_en: str
    headline_kn: str
    explanation_en: str
    explanation_kn: str
    crop_specific_notes: List[str]
    precautions_en: List[str]
    precautions_kn: List[str]
    profit_optimization: HarvestProfitOptimizationOut


class HarvestProtectionSummaryOut(BaseModel):
    location_label: str
    weather_freshness: str
    decisions: List[HarvestProtectionItemOut]
