"""Crop recommendation and growth monitoring schemas."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class CropRecommendRequest(BaseModel):
    season: str = Field(default="Kharif", max_length=32)
    water_availability: str = Field(default="moderate", max_length=32)
    budget_level: str = Field(default="moderate", max_length=32)
    include_horticulture: bool = True
    avg_temp_c: Optional[float] = Field(default=None, ge=-5.0, le=55.0)
    annual_rainfall_mm: Optional[float] = Field(default=None, ge=0.0, le=6000.0)
    state_override: Optional[str] = Field(default=None, max_length=80)


class CropRecommendItem(BaseModel):
    crop_name: str
    category: str
    suitability_score: int
    reasons: List[str]
    duration_days: str
    water_requirement: str
    nutrient_needs: str
    estimated_cost_per_acre_inr: str
    expected_yield_per_acre: str
    market_value_note: str


class CropRecommendResponse(BaseModel):
    season: str
    location_summary: str
    soil_source_used: str
    missing_soil_fields: List[str]
    recommendations: List[CropRecommendItem]


class CropStageGuidanceOut(BaseModel):
    stage_key: str
    stage_label: str
    day_range: str
    irrigation_advice: str
    nutrient_advice: str
    cultivation_tasks: List[str]


class TrackedCropCreate(BaseModel):
    crop_name: str = Field(min_length=2, max_length=80)
    variety: Optional[str] = Field(default=None, max_length=80)
    category: str = Field(default="cereal", max_length=40)
    sowing_date: date
    acreage: float = Field(default=1.0, gt=0.0, le=5000.0)
    irrigation_type: str = Field(default="drip", max_length=40)
    notes: Optional[str] = Field(default=None, max_length=500)


class TrackedCropUpdate(BaseModel):
    current_stage: Optional[str] = Field(default=None, max_length=60)
    completed_tasks: Optional[List[str]] = None
    status: Optional[str] = Field(default=None, max_length=24)
    irrigation_type: Optional[str] = Field(default=None, max_length=40)
    notes: Optional[str] = Field(default=None, max_length=500)


class TrackedCropOut(BaseModel):
    id: int
    farmer_id: int
    crop_name: str
    variety: Optional[str] = None
    category: str
    sowing_date: date
    acreage: float
    irrigation_type: str
    current_stage: str
    completed_tasks: List[str]
    status: str
    notes: Optional[str] = None
    days_since_sowing: int
    stage_guidance: Optional[CropStageGuidanceOut] = None
